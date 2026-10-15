"""Shared sign-in helper for the scripts: returns Authorization headers for a demo staff account.

Reads STAFF_DEMO_PASSWORD from the repo-root .env. With AUTH_REQUIRED=0 the headers are simply ignored by the server.
"""
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _env(key: str) -> str | None:
    p = ROOT / ".env"
    if not p.exists():
        return None
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip()
    return None


def staff_headers(base: str, staff_id: str) -> dict:
    pw = _env("STAFF_DEMO_PASSWORD")
    if not pw:
        return {}
    req = urllib.request.Request(f"{base}/api/auth/staff", method="POST",
                                 data=json.dumps({"staff_id": staff_id, "password": pw}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return {"Authorization": "Bearer " + json.loads(r.read())["token"]}
    except Exception:  # noqa: BLE001  (server without auth endpoints, or auth disabled)
        return {}
