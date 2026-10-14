"""CAN citizen profiles (contract v1.5). Written by Person 1 with the CAN endpoints (comms P1→P2 #0013)."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _office(client) -> str:
    return client.get("/api/offices").json()[0]["id"]


def test_create_then_find_by_phone(client):
    body = {"name": "karthik  r", "dob": "1998-04-12", "phone": "+91 98765 11111", "pin_code": "641402"}
    r = client.post("/api/citizens", json=body)
    assert r.status_code == 201
    c = r.json()
    assert c["can"].startswith("CAN") and len(c["can"]) == 13
    assert c["name"] == "KARTHIK R" and c["phone_masked"] == "98XXXXXX11"
    again = client.post("/api/citizens", json={**body, "name": "SOMEONE ELSE"})
    assert again.status_code == 200 and again.json()["can"] == c["can"]  # one CAN per phone, never edited
    assert again.json()["name"] == "KARTHIK R"
    assert client.get(f"/api/citizens/{c['can'].lower()}").json()["can"] == c["can"]


def test_raw_phone_never_stored(client):
    client.post("/api/citizens", json={"name": "MEENA S", "phone": "9123412345"})
    con = sqlite3.connect(get_settings().db_url.replace("sqlite:///", ""))
    dump = "\n".join(con.iterdump())
    con.close()
    assert "9123412345" not in dump


def test_application_from_can_uses_profile(client):
    c = client.post("/api/citizens", json={"name": "R. PRIYA", "dob": "2001-02-03", "phone": "9000011111"}).json()
    r = client.post("/api/applications", json={"can": c["can"], "service": "income_certificate",
                                               "office_id": _office(client), "citizen_name": "TYPO NAME"})
    assert r.status_code == 201
    a = r.json()
    assert a["can_id"] == c["can"] and a["citizen_name"] == "R. PRIYA" and a["citizen_dob"] == "2001-02-03"
    assert client.get(f"/api/applications/{a['id']}").json()["can_id"] == c["can"]


def test_errors(client):
    assert client.get("/api/citizens/CAN2026999999").status_code == 404
    bad = client.post("/api/applications", json={"can": "CAN2026999999", "service": "income_certificate",
                                                 "office_id": _office(client)})
    assert bad.status_code == 400 and bad.json()["error"]["code"] == "UNKNOWN_CAN"
    missing = client.post("/api/applications", json={"service": "income_certificate", "office_id": _office(client)})
    assert missing.status_code == 422
    assert client.post("/api/citizens", json={"name": "X", "phone": "12345"}).status_code == 422
    assert client.post("/api/citizens", json={"name": "X", "phone": "9876543210", "dob": "12/04/1998"}).status_code == 422


def test_old_flow_without_can_still_works(client):
    r = client.post("/api/applications", json={"citizen_name": "KARTHIK R", "phone": "9876543221",
                                               "service": "community_certificate", "office_id": _office(client)})
    assert r.status_code == 201 and r.json()["can_id"] is None
