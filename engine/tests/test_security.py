"""Server-side security: every hole from the audit must be closed when AUTH_REQUIRED=1."""
import time

import pytest
from fastapi.testclient import TestClient

from app.core.auth import Principal, issue_token, verify_token
from app.core.config import get_settings
from app.main import app

PW = "test-staff-password-123"


@pytest.fixture()
def client(monkeypatch):
    from app.core import auth as auth_mod
    auth_mod._hits.clear()  # each test starts with fresh rate-limit windows (all tests share one client IP)
    monkeypatch.setattr(get_settings(), "auth_required", True)
    with TestClient(app) as c:
        yield c


def staff(c, staff_id):
    r = c.post("/api/auth/staff", json={"staff_id": staff_id, "password": PW})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def citizen(c, phone):
    otp = c.post("/api/auth/otp/request", json={"phone": phone}).json()["demo_otp"]
    r = c.post("/api/auth/otp/verify", json={"phone": phone, "otp": otp})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_public_endpoints_stay_open(client):
    for path in ("/api/health", "/api/offices", "/api/metrics/detection"):
        assert client.get(path).status_code == 200


@pytest.mark.parametrize("method,path", [
    ("GET", "/api/applications"), ("GET", "/api/applications/app_x"), ("GET", "/api/documents/doc_x/image"),
    ("PATCH", "/api/applications/app_x"), ("GET", "/api/citizens/CAN2026000001"), ("GET", "/api/notifications"),
    ("GET", "/api/issues"), ("GET", "/api/alerts"), ("GET", "/api/metrics/operations"), ("POST", "/api/citizens"),
    ("POST", "/api/applications"),
])
def test_anonymous_is_rejected(client, method, path):
    r = client.request(method, path, json={})
    assert r.status_code == 401 and r.json()["error"]["code"] == "NOT_SIGNED_IN"


def test_bad_password_and_forged_or_expired_tokens(client):
    assert client.post("/api/auth/staff", json={"staff_id": "TAH-SULUR-001", "password": "wrong"}).status_code == 401
    forged = {"Authorization": "Bearer eyJyIjoidGFoc2lsZGFyIn0.c2lnbmF0dXJl"}
    assert client.get("/api/applications", headers=forged).status_code == 401
    token, _ = issue_token(Principal(role="vao", sub="VAO-SULUR-014"))
    payload, sig = token.split(".")
    tampered = payload[:-2] + ("AA" if payload[-2:] != "AA" else "BB") + "." + sig
    assert verify_token(tampered) is None
    p = verify_token(token)
    p.exp = int(time.time()) - 1
    assert verify_token(token) is not None  # real token still valid; expiry is inside the signed payload


def test_login_is_rate_limited(client):
    codes = [client.post("/api/auth/staff", json={"staff_id": "RI-SULUR-007", "password": f"guess{i}"}).status_code
             for i in range(8)]
    assert 429 in codes


def test_roles_and_ownership(client):
    op = staff(client, "ESV-SULUR2-031")
    vao, tah = staff(client, "VAO-SULUR-014"), staff(client, "TAH-SULUR-001")
    # operator creates at own centre only
    bad = client.post("/api/applications", headers=op, json={"citizen_name": "A B", "phone": "9876500001",
                                                             "service": "income_certificate", "office_id": "off_pollachi_to"})
    assert bad.status_code == 403
    a = client.post("/api/applications", headers=op, json={"citizen_name": "A B", "phone": "9876500001",
                                                           "service": "income_certificate", "office_id": "off_sulur_es2"})
    assert a.status_code == 201
    app_id = a.json()["id"]
    # citizens cannot list everything or read others' applications
    me = citizen(client, "9123400077")
    assert client.get("/api/applications", headers=me).status_code == 403
    assert client.get(f"/api/applications/{app_id}", headers=me).status_code == 403
    # a citizen can only create a CAN for their own phone, and apply with their own CAN
    assert client.post("/api/citizens", headers=me, json={"name": "X Y", "phone": "9000000001"}).status_code == 403
    can = client.post("/api/citizens", headers=me, json={"name": "MY NAME", "phone": "9123400077"}).json()["can"]
    other_can = client.post("/api/citizens", headers=op, json={"name": "OTHER", "phone": "9000000002"}).json()["can"]
    assert client.get(f"/api/citizens/{other_can}", headers=me).status_code == 404
    assert client.post("/api/applications", headers=me, json={"can": other_can, "service": "income_certificate",
                                                              "office_id": "off_sulur_es2"}).status_code == 403
    mine = client.post("/api/applications", headers=me, json={"can": can, "service": "income_certificate",
                                                              "office_id": "off_sulur_es2"})
    assert mine.status_code == 201
    assert client.get(f"/api/applications/{mine.json()['id']}", headers=me).status_code == 200
    # officers: VAO cannot approve; role in the body cannot be spoofed
    assert client.patch(f"/api/applications/{app_id}", headers=vao, json={"action": "approve"}).status_code == 403
    assert client.patch(f"/api/applications/{app_id}", headers=vao,
                        json={"action": "approve", "role": "tahsildar"}).status_code == 403
    assert client.get("/api/applications", headers=tah).status_code == 200
    # operators: other centres' notices are off limits
    assert client.get("/api/alerts?office_id=off_pollachi_to", headers=op).status_code == 403
    assert client.get("/api/alerts?office_id=off_sulur_es2", headers=op).status_code == 200


def test_security_headers(client):
    h = client.get("/api/health").headers
    assert h["x-frame-options"] == "DENY" and h["x-content-type-options"] == "nosniff"
    assert "frame-ancestors 'none'" in h["content-security-policy"] and h["cache-control"] == "no-store"


def test_random_can_ids(client):
    op = staff(client, "ESV-SULUR2-031")
    cans = [client.post("/api/citizens", headers=op, json={"name": "N", "phone": f"98765000{i:02d}"}).json()["can"]
            for i in range(3)]
    nums = sorted(int(c[-6:]) for c in cans)
    assert not (nums[1] == nums[0] + 1 and nums[2] == nums[1] + 1)  # not sequential


def test_successful_logins_do_not_lock_the_account(client):
    for _ in range(8):  # rehearsals: many good sign-ins in a row must keep working
        assert client.post("/api/auth/staff", json={"staff_id": "VAO-SULUR-014", "password": PW}).status_code == 200


def test_failed_logins_lock_that_id(client):
    codes = [client.post("/api/auth/staff", json={"staff_id": "TAH-SULUR-001", "password": "nope"}).status_code
             for _ in range(7)]
    assert codes[:5] == [401] * 5 and 429 in codes[5:]


def test_demo_number_otp_not_locked_but_real_numbers_are(client):
    assert all(client.post("/api/auth/otp/request", json={"phone": "9876543221"}).status_code == 200 for _ in range(6))
    real = [client.post("/api/auth/otp/request", json={"phone": "9123455555"}).status_code for _ in range(5)]
    assert 429 in real


def test_any_department_officer_and_any_centre_operator_can_sign_in_with_the_password(client):
    for sid, role, office in [("VAO-POLLACHI-002", "vao", None), ("RI-ANNUR-011", "ri", None),
                              ("TAH-VALPARAI-001", "tahsildar", None), ("ESV-POLLACHI-001", "operator", "off_pollachi_es"),
                              ("ESV-POLLACHITO-007", "operator", "off_pollachi_to"),
                              ("ESV-SULUR1-010", "operator", "off_sulur_es1")]:
        r = client.post("/api/auth/staff", json={"staff_id": sid, "password": PW})
        assert r.status_code == 200, (sid, r.text)
        assert r.json()["role"] == role and r.json()["office_id"] == office
    for sid in ("ESV-NOWHERE-001", "ABC-SULUR-001", "VAO-POLLACHI-02"):
        assert client.post("/api/auth/staff", json={"staff_id": sid, "password": PW}).status_code == 401
    assert client.post("/api/auth/staff", json={"staff_id": "VAO-POLLACHI-002", "password": "wrong"}).status_code == 401
