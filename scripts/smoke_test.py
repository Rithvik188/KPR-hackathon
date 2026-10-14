"""End-to-end smoke test through the HTTP API (needs Person 2's ops endpoints, i.e. after Sync 2).

Creates an application, uploads demo images 01 -> 02 -> 03 -> 05 and checks the statuses:
fixable, accepted, accepted, accepted, and the application ends as ready_for_officer.

Usage (backend running):  python scripts/smoke_test.py [--base http://localhost:8000]
"""
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "demo" / "images"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://localhost:8000"


def call(method: str, path: str, body: bytes | None = None, ctype: str | None = None):
    req = urllib.request.Request(BASE + path, data=body, method=method,
                                 headers={"Content-Type": ctype} if ctype else {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw and r.headers.get_content_type() == "application/json" else raw)
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def upload(app_id: str, file: Path, declared: str):
    b = uuid.uuid4().hex
    body = (f'--{b}\r\nContent-Disposition: form-data; name="declared_type"\r\n\r\n{declared}\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{file.name}"\r\n'
            f"Content-Type: image/jpeg\r\n\r\n").encode() + file.read_bytes() + f"\r\n--{b}--\r\n".encode()
    return call("POST", f"/api/applications/{app_id}/documents", body, f"multipart/form-data; boundary={b}")


def main() -> int:
    ok = True

    def expect(label: str, cond: bool, detail="") -> None:
        nonlocal ok
        print(f"{'PASS' if cond else 'FAIL'}  {label} {detail}")
        ok &= cond

    st, offices = call("GET", "/api/offices")
    if st != 200 or not offices:
        print(f"FAIL  /api/offices -> {st}; ops endpoints not available yet")
        return 1
    payload = json.dumps({"citizen_name": "KARTHIK R", "phone": "9876543221", "service": "community_certificate",
                          "office_id": offices[0]["id"]}).encode()
    st, app = call("POST", "/api/applications", payload, "application/json")
    expect("create application", st == 201, f"(HTTP {st})")
    if st != 201:
        return 1
    app_id = app["id"]
    steps = [("01_aadhaar_front_blurry.jpg", "aadhaar_front", "fixable"),
             ("02_aadhaar_front_clean.jpg", "aadhaar_front", "accepted"),
             ("03_aadhaar_back_clean.jpg", "aadhaar_back", "accepted"),
             ("05_pan_clean_initials.jpg", "pan", "accepted")]
    last = None
    for name, declared, want in steps:
        st, res = upload(app_id, DEMO / name, declared)
        got = res["validation"]["status"] if st == 200 else f"HTTP {st}"
        expect(f"upload {name}", got == want, f"-> {got}")
        last = res if st == 200 else last
        if st == 200:
            text = json.dumps(res)
            expect("  no 12-digit run in response", not re.search(r"(?<![0-9a-f])\d{12}(?![0-9a-f])", text))
    if last:
        expect("application ready_for_officer", last["application"]["status"] == "ready_for_officer",
               f"-> {last['application']['status']}")
        expect("consistency likely_match", last["consistency"]["name_tier"] == "likely_match",
               f"-> {last['consistency']['name_tier']}")
    st, lst = call("GET", "/api/applications?status=ready_for_officer")
    expect("appears in officer queue", st == 200 and any(i["id"] == app_id for i in lst.get("items", [])))
    st, detail = call("GET", f"/api/applications/{app_id}")
    doc_id = detail["documents"][-1]["id"] if st == 200 and detail.get("documents") else None
    if doc_id:
        st, _ = call("GET", f"/api/documents/{doc_id}/image")
        expect("officer can see card image", st == 200)
    st, _ = call("PATCH", f"/api/applications/{app_id}", json.dumps({"action": "approve"}).encode(),
                 "application/json")
    expect("approve", st == 200, f"(HTTP {st})")
    if doc_id:
        st, _ = call("GET", f"/api/documents/{doc_id}/image")
        expect("image deleted after decision (404)", st == 404, f"(HTTP {st})")
    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
