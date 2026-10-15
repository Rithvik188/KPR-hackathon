"""Server-side authentication: staff passwords (PBKDF2), citizen OTP, signed expiring session tokens, rate limits.

Prototype scope, stated honestly (docs/SECURITY.md): demo staff accounts share one password from `.env`
(STAFF_DEMO_PASSWORD, never shown in the UI), and the citizen OTP is "delivered" through the mock-SMS channel. A real
deployment replaces both with government SSO (e-Pramaan) and a real SMS gateway; the token checks and the permission
table stay the same.
"""
import base64
import re
import hashlib
import hmac
import json
import secrets
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass

from app.core.config import get_settings

STAFF_ROLES = ("vao", "ri", "tahsildar")
ROLES = ("citizen", "operator") + STAFF_ROLES

# Demo staff directory (IDs match the department/operator login screens). Passwords are NOT stored here.
STAFF = {
    "VAO-SULUR-014": {"role": "vao", "name": "S. Meena", "office_id": None},
    "RI-SULUR-007": {"role": "ri", "name": "K. Rajan", "office_id": None},
    "TAH-SULUR-001": {"role": "tahsildar", "name": "A. Selvi", "office_id": None},
    "ESV-SULUR2-031": {"role": "operator", "name": "P. Divya", "office_id": "off_sulur_es2"},
    "ESV-PVT-112": {"role": "operator", "name": "M. Farooq", "office_id": "off_saibaba_es"},
}
_DEPT_ID = re.compile(r"^(VAO|RI|TAH)-[A-Z0-9]{2,20}-\d{3}$")
_OP_ID = re.compile(r"^ESV-([A-Z0-9]{2,20})-\d{3}$")
_DEPT_ROLE = {"VAO": "vao", "RI": "ri", "TAH": "tahsildar"}


def office_key(office_id: str) -> str:
    """Centre code in operator IDs: e-Sevai centres use their place (+ number), taluk offices add "TO".
    off_sulur_es2 -> SULUR2, off_pollachi_es -> POLLACHI, off_pollachi_to -> POLLACHITO, off_cbe_north_to -> CBENORTHTO.
    """
    k = office_id.removeprefix("off_")
    m = re.match(r"^(.*)_(es|to)(\d*)$", k)
    if m:
        k = m.group(1) + m.group(3) + ("TO" if m.group(2) == "to" else "")
    return k.replace("_", "").upper()


def lookup_staff(staff_id: str) -> dict | None:
    """Any department officer (VAO-/RI-/TAH-<AREA>-NNN) or any e-Sevai operator (ESV-<CENTRE>-NNN, bound to that
    centre). Named demo accounts in STAFF keep their names. Everyone still needs the staff password."""
    sid = staff_id.strip().upper()
    if sid in STAFF:
        return STAFF[sid]
    m = _DEPT_ID.match(sid)
    if m:
        return {"role": _DEPT_ROLE[m.group(1)], "name": sid, "office_id": None}
    m = _OP_ID.match(sid)
    if m:
        from sqlmodel import Session, select

        from app.core.db import engine
        from app.core.models import Office

        with Session(engine) as session:
            for oid in session.exec(select(Office.id)).all():
                if office_key(oid) == m.group(1):
                    return {"role": "operator", "name": sid, "office_id": oid}
    return None


TOKEN_TTL = {"citizen": 2 * 3600, "operator": 10 * 3600, "vao": 10 * 3600, "ri": 10 * 3600, "tahsildar": 10 * 3600}
OTP_TTL = 300
OTP_MAX_TRIES = 5


def _key(purpose: str) -> bytes:
    # Derived from the server secret, so tokens cannot be forged without it and no new secret needs distributing.
    return hmac.new(get_settings().aadhaar_hmac_secret.encode(), f"sevaicheck:{purpose}:v1".encode(),
                    hashlib.sha256).digest()


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# ---------------- passwords ----------------

_salt_hash_cache: dict[str, bytes] = {}


def _password_hash(password: str) -> bytes:
    salt = _key("staff-password-salt")
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)


def check_staff_password(staff_id: str, password: str) -> bool:
    expected_pw = get_settings().staff_demo_password
    if not expected_pw or lookup_staff(staff_id) is None:
        _password_hash(password or "x")  # constant-ish time for unknown IDs
        return False
    if "expected" not in _salt_hash_cache:
        _salt_hash_cache["expected"] = _password_hash(expected_pw)
    return hmac.compare_digest(_password_hash(password or ""), _salt_hash_cache["expected"])


# ---------------- tokens ----------------

@dataclass
class Principal:
    role: str
    sub: str  # staff ID, or the citizen's phone HMAC (never the raw phone)
    name: str | None = None
    office_id: str | None = None
    exp: int = 0

    @property
    def is_staff(self) -> bool:
        return self.role in STAFF_ROLES


def issue_token(p: Principal) -> tuple[str, int]:
    exp = int(time.time()) + TOKEN_TTL[p.role]
    payload = _b64(json.dumps({"r": p.role, "s": p.sub, "n": p.name, "o": p.office_id, "e": exp,
                               "j": secrets.token_hex(6)}, separators=(",", ":")).encode())
    sig = _b64(hmac.new(_key("session"), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}", exp


def verify_token(token: str) -> Principal | None:
    try:
        payload, sig = token.split(".", 1)
        good = _b64(hmac.new(_key("session"), payload.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, good):
            return None
        d = json.loads(_unb64(payload))
        if d["e"] < time.time() or d["r"] not in ROLES:
            return None
        return Principal(role=d["r"], sub=d["s"], name=d.get("n"), office_id=d.get("o"), exp=d["e"])
    except Exception:  # noqa: BLE001
        return None


# ---------------- citizen OTP ----------------

_otp_lock = threading.Lock()
_otps: dict[str, tuple[bytes, float, int]] = {}  # phone_hmac -> (hash(otp), expiry, tries)


def new_otp(phone_key: str) -> str:
    code = f"{secrets.randbelow(1_000_000):06d}"
    with _otp_lock:
        _otps[phone_key] = (hmac.new(_key("otp"), code.encode(), hashlib.sha256).digest(), time.time() + OTP_TTL, 0)
    return code


def check_otp(phone_key: str, code: str) -> bool:
    with _otp_lock:
        rec = _otps.get(phone_key)
        if rec is None:
            return False
        digest, exp, tries = rec
        if time.time() > exp or tries >= OTP_MAX_TRIES:
            _otps.pop(phone_key, None)
            return False
        ok = hmac.compare_digest(digest, hmac.new(_key("otp"), (code or "").encode(), hashlib.sha256).digest())
        if ok:
            _otps.pop(phone_key, None)  # single use
        else:
            _otps[phone_key] = (digest, exp, tries + 1)
        return ok


# ---------------- rate limiting ----------------

_rl_lock = threading.Lock()
_hits: dict[str, deque] = defaultdict(deque)


def recent_count(key: str, window_s: int) -> int:
    """Events recorded for `key` in the last `window_s` seconds (without recording a new one)."""
    now = time.time()
    with _rl_lock:
        q = _hits[key]
        while q and q[0] < now - window_s:
            q.popleft()
        return len(q)


def record(key: str) -> None:
    with _rl_lock:
        _hits[key].append(time.time())


def rate_limited(key: str, limit: int, window_s: int) -> bool:
    """True if `key` exceeded `limit` events in the last `window_s` seconds (sliding window, in memory)."""
    now = time.time()
    with _rl_lock:
        q = _hits[key]
        while q and q[0] < now - window_s:
            q.popleft()
        if len(q) >= limit:
            return True
        q.append(now)
        return False
