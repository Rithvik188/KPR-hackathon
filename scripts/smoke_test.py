"""End-to-end smoke test through the HTTP API (needs Person 2's ops endpoints).

Creates a community-certificate application (operator types "KARTHIK R", DOB 1998-04-12), uploads demo images
01 -> 02 -> 03 -> 05 -> 10 (parent's community certificate) and checks: fixable, accepted x4, ready_for_officer,
likely_match, the form check (contract v1.4) and, when the server has stages, the VAO -> RI -> Tahsildar chain.
Checks for v1.4 features are skipped (not failed) on a server that does not have them yet.

Usage (backend running):  python scripts/smoke_test.py [--base http://127.0.0.1:8000]
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
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://127.0.0.1:8000"


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
    payload = json.dumps({"citizen_name": "KARTHIK R", "citizen_dob": "1998-04-12", "phone": "9876543221",
                          "service": "community_certificate", "office_id": offices[0]["id"]}).encode()
    st, app = call("POST", "/api/applications", payload, "application/json")
    expect("create application", st == 201, f"(HTTP {st})")
    if st != 201:
        return 1
    app_id = app["id"]
    steps = [("01_aadhaar_front_blurry.jpg", "aadhaar_front", "fixable"),
             ("02_aadhaar_front_clean.jpg", "aadhaar_front", "accepted"),
             ("03_aadhaar_back_clean.jpg", "aadhaar_back", "accepted"),
             ("05_pan_clean_initials.jpg", "pan", "accepted"),
             ("10_parent_community_certificate.jpg", "parent_community_certificate", "accepted")]
    last = None
    for name, declared, want in steps:
        st, res = upload(app_id, DEMO / name, declared)
        if declared == "parent_community_certificate" and st != 200:
            print(f"SKIP  upload {name} (HTTP {st}: server predates contract v1.4 supporting documents)")
            continue
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
        fc = last["consistency"].get("form_check")
        if fc:
            expect("form check: typed name matches documents", fc.get("name_tier") == "match", f"-> {fc}")
            expect("form check: typed DOB matches documents", fc.get("dob_match") is True, f"-> {fc}")
        else:
            print("SKIP  form check (server predates contract v1.4 form_check)")
    # Seeded data puts thousands of applications in the queue: page through this office's queue.
    found, offset = False, 0
    while not found:
        st, lst = call("GET", f"/api/applications?status=ready_for_officer&office_id={app['office_id']}"
                              f"&limit=200&offset={offset}")
        items = lst.get("items", []) if st == 200 else []
        found = any(i["id"] == app_id for i in items)
        offset += 200
        if not items or offset >= lst.get("total", 0):
            break
    expect("appears in officer queue", found)
    st, detail = call("GET", f"/api/applications/{app_id}")
    doc_id = detail["documents"][-1]["id"] if st == 200 and detail.get("documents") else None
    if doc_id:
        st, _ = call("GET", f"/api/documents/{doc_id}/image")
        expect("officer can see card image", st == 200)
    def patch(body: dict):
        return call("PATCH", f"/api/applications/{app_id}", json.dumps(body).encode(), "application/json")

    if last and last["application"].get("stage") == "vao":  # contract v1.4 officer chain
        st, summ = patch({"action": "approve", "role": "vao"})
        expect("VAO cannot approve (409)", st == 409, f"(HTTP {st})")
        st, summ = patch({"action": "forward", "role": "vao"})
        expect("VAO forwards -> RI", st == 200 and summ.get("stage") == "ri", f"(HTTP {st})")
        st, summ = patch({"action": "forward", "role": "vao"})
        expect("stale role rejected (409 STAGE_MISMATCH)", st == 409, f"(HTTP {st})")
        st, summ = patch({"action": "forward", "role": "ri"})
        expect("RI forwards -> Tahsildar", st == 200 and summ.get("stage") == "tahsildar", f"(HTTP {st})")
        st, _ = patch({"action": "approve", "role": "tahsildar"})
        expect("Tahsildar approves", st == 200, f"(HTTP {st})")
    else:
        print("SKIP  stage chain (server predates contract v1.4 stages)")
        st, _ = patch({"action": "approve"})
        expect("approve", st == 200, f"(HTTP {st})")
    if doc_id:
        st, _ = call("GET", f"/api/documents/{doc_id}/image")
        expect("image deleted after decision (404)", st == 404, f"(HTTP {st})")
    print("\nSMOKE TEST", "PASSED" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
