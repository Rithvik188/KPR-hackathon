"""Compare live API response shapes with contract/fixtures. Prints PASS / FAIL / SKIP per endpoint.

Usage (backend running):  python scripts/contract_check.py [--base http://localhost:8000]
Exit code 1 if any endpoint FAILs. 404 (not implemented yet) is a SKIP.
"""
import io
import json
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "contract" / "fixtures"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:8000"

# Free-form objects whose keys legitimately vary.
FREE_FORM = {"evidence", "fields"}


def http(method: str, path: str, body: bytes | None = None, headers: dict | None = None):
    req = urllib.request.Request(BASE + path, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read() or b"null")
        except json.JSONDecodeError:
            return e.code, None


def compare(live, fixture, path="$") -> list[str]:
    """Recursive key-set comparison. None on either side is accepted (nullable fields)."""
    if live is None or fixture is None:
        return []
    if isinstance(fixture, dict):
        if not isinstance(live, dict):
            return [f"{path}: expected object, got {type(live).__name__}"]
        errs = []
        missing = set(fixture) - set(live)
        extra = set(live) - set(fixture)
        if missing:
            errs.append(f"{path}: missing keys {sorted(missing)}")
        if extra:
            errs.append(f"{path}: unexpected keys {sorted(extra)}")
        for k in set(fixture) & set(live):
            if k not in FREE_FORM:
                errs += compare(live[k], fixture[k], f"{path}.{k}")
        return errs
    if isinstance(fixture, list):
        if not isinstance(live, list):
            return [f"{path}: expected array, got {type(live).__name__}"]
        if live and fixture:
            return compare(live[0], fixture[0], f"{path}[0]")
        return []
    num = (int, float)
    if isinstance(fixture, bool) != isinstance(live, bool) or (
            isinstance(fixture, num) and not isinstance(live, num)) or (
            isinstance(fixture, str) and not isinstance(live, str)):
        return [f"{path}: type {type(live).__name__} != fixture {type(fixture).__name__}"]
    return []


def tiny_jpeg() -> bytes:
    try:
        from PIL import Image
    except ImportError:
        sys.exit("Pillow is required (run with engine/.venv python)")
    buf = io.BytesIO()
    Image.new("RGB", (64, 40), (200, 200, 200)).save(buf, "JPEG")
    return buf.getvalue()


def multipart(fields: dict, file_bytes: bytes) -> tuple[bytes, str]:
    b = uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="t.jpg"\r\n'
                 f'Content-Type: image/jpeg\r\n\r\n'.encode() + file_bytes + b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={b}"


def fixture(name: str):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


results: list[tuple[str, str, list[str]]] = []


def check(label: str, status: int, live, fix) -> None:
    if status == 404:
        results.append((label, "SKIP", ["not yet implemented (404)"]))
    elif status >= 400:
        results.append((label, "FAIL", [f"HTTP {status}: {live}"]))
    else:
        errs = compare(live, fix)
        results.append((label, "PASS" if not errs else "FAIL", errs))


def main() -> int:
    try:
        st, live = http("GET", "/api/health")
    except urllib.error.URLError as e:
        print(f"Backend not reachable at {BASE}: {e}")
        return 1
    check("GET /api/health", st, live, {"status": "ok", "ocr_engine": "easyocr", "ocr_gpu": False, "ocr_ready": False, "version": "1.1"})
    if st == 200 and live.get("status") != "ok":
        results[-1] = ("GET /api/health", "FAIL", [f"status={live.get('status')}"])

    body, ctype = multipart({"declared_type": "pan"}, tiny_jpeg())
    st, live = http("POST", "/api/validate", body, {"Content-Type": ctype})
    fx = fixture("validate_fixable.json" if (live or {}).get("fields") is None else "validate_accepted.json")
    check("POST /api/validate", st, live, fx)

    for label, path, fx_name in [
        ("GET /api/metrics/detection", "/api/metrics/detection", "metrics_detection.json"),
        ("GET /api/offices", "/api/offices", "offices.json"),
        ("GET /api/applications", "/api/applications", "applications_list.json"),
        ("GET /api/alerts", "/api/alerts", "alerts.json"),
        ("GET /api/metrics/operations", "/api/metrics/operations", "metrics_operations.json"),
        ("GET /api/issues", "/api/issues", "issues.json"),
        ("GET /api/notifications", "/api/notifications", "notifications.json"),
    ]:
        st, live = http("GET", path)
        check(label, st, live, fixture(fx_name))
        if label == "GET /api/applications" and st == 200 and live.get("items"):
            app_id = live["items"][0]["id"]
            st2, live2 = http("GET", f"/api/applications/{app_id}")
            check("GET /api/applications/{id}", st2, live2, fixture("application_detail.json"))

    failed = False
    for label, verdict, errs in results:
        print(f"{verdict:4}  {label}")
        for e in errs:
            print(f"        {e}")
        failed |= verdict == "FAIL"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
