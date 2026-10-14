"""End-to-end ops flow through the API. The engine is faked here (accepted / BLUR outcomes), so these tests
check ops behaviour only and keep passing when Person 1's real validation replaces the stubs.
"""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

import app.ops.routers.documents as documents_router
import app.ops.service as ops_service
from app.main import app
from app.validation.messages import make_issue
from app.validation.types import (ConsistencyResult, ExtractedDoc, Quality, Timings, ValidationOutcome,
                                  ValidationResult)

FIELDS = {
    "aadhaar_front": {"id_number_display": "XXXX XXXX 4321", "name": "R. KARTHIK", "dob": "1998-04-12",
                      "gender": "M", "father_name": None},
    "aadhaar_back": {"id_number_display": "XXXX XXXX 4321", "pin_code": "641402"},
    "pan": {"id_number_display": "ABCPK1234F", "name": "KARTHIK RAJENDRAN", "dob": "1998-04-12", "gender": None,
            "father_name": "RAJENDRAN"},
}


def jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (1000, 630), (230, 230, 230)).save(buf, "JPEG")
    return buf.getvalue()


def accepted_outcome(image: bytes, declared_type: str | None = None) -> ValidationOutcome:
    fields = FIELDS[declared_type or "aadhaar_front"]
    result = ValidationResult(
        doc_type=declared_type or "aadhaar_front", declared_type=declared_type, status="accepted", issues=[],
        quality=Quality(card_found=True, blur_score=300.0, passed=True), fields=fields,
        ocr={"mean_confidence": 0.93, "id_number_confidence": 0.95}, timings_ms=Timings(quality=150, ocr=900, total=1050))
    extracted = ExtractedDoc(doc_type=result.doc_type, declared_type=declared_type, name=fields.get("name"),
                             dob=fields.get("dob"), id_last4="4321")
    return ValidationOutcome(result=result, card_jpeg=image, extracted=extracted)


def blurry_outcome(_: bytes, declared_type: str | None = None) -> ValidationOutcome:
    issues = [make_issue("BLUR", {"blur_score": 41.2, "threshold": 100})]
    return ValidationOutcome(result=ValidationResult(
        doc_type="unknown", declared_type=declared_type, status="fixable", issues=issues,
        quality=Quality(card_found=True, blur_score=41.2, passed=False), timings_ms=Timings(quality=180, ocr=0, total=195)))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(documents_router, "validate_image", accepted_outcome)
    monkeypatch.setattr(documents_router, "find_duplicates", lambda *a, **k: [])
    monkeypatch.setattr(ops_service, "check_consistency", lambda docs: ConsistencyResult(name_tier="not_enough_data"))
    with TestClient(app) as c:
        yield c


def create(client, name="R. Karthik") -> dict:
    res = client.post("/api/applications", json={"citizen_name": name, "phone": "+91 98765 43221",
                                                  "service": "community_certificate", "office_id": "off_sulur_es2"})
    assert res.status_code == 201, res.text
    return res.json()


def upload(client, app_id: str, declared_type: str) -> dict:
    res = client.post(f"/api/applications/{app_id}/documents", data={"declared_type": declared_type},
                      files={"file": ("card.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()


def test_create_masks_phone_and_starts_submitted(client):
    created = create(client)
    assert created["status"] == "submitted"
    assert created["phone_masked"] == "98XXXXXX21"
    assert created["citizen_name"] == "R. KARTHIK"
    assert 71.9 < created["sla_hours_left"] <= 72
    assert created["office_name"] == "e-Sevai Centre – Sulur 2"


def test_full_loop_blur_retake_ready_approve_deletes_images(client, monkeypatch):
    app_id = create(client)["id"]

    # Attempt 1 is blurry: needs_fix, one SMS.
    monkeypatch.setattr(documents_router, "validate_image", blurry_outcome)
    first = upload(client, app_id, "aadhaar_front")
    assert first["validation"]["status"] == "fixable"
    assert first["validation"]["document_id"] == first["document_id"]
    assert first["application"]["status"] == "needs_fix"
    assert first["application"]["flag_codes"] == ["BLUR"]

    # Retake, then back and PAN.
    monkeypatch.setattr(documents_router, "validate_image", accepted_outcome)
    second = upload(client, app_id, "aadhaar_front")
    assert second["validation"]["status"] == "accepted"
    assert second["application"]["resubmissions"] == 1
    upload(client, app_id, "aadhaar_back")
    last = upload(client, app_id, "pan")
    assert last["application"]["status"] == "ready_for_officer"
    assert last["application"]["doc_count"] == 3

    # Ready applications come first in the officer queue.
    listing = client.get("/api/applications").json()
    assert listing["items"][0]["status"] == "ready_for_officer"

    detail = client.get(f"/api/applications/{app_id}").json()
    assert [d["doc_type"] for d in detail["documents"]] == ["aadhaar_front", "aadhaar_back", "pan"]
    assert all(d["image_available"] for d in detail["documents"])
    image = client.get(f"/api/documents/{detail['documents'][0]['id']}/image")
    assert image.status_code == 200 and image.headers["content-type"] == "image/jpeg"
    events = [h["event"] for h in detail["history"]]
    assert events[0] == "application_created" and "sent_to_officer" in events

    approved = client.patch(f"/api/applications/{app_id}", json={"action": "approve"})
    assert approved.status_code == 200 and approved.json()["status"] == "approved"
    for doc in detail["documents"]:
        assert client.get(f"/api/documents/{doc['id']}/image").status_code == 404
    after = client.get(f"/api/applications/{app_id}").json()
    assert after["decision"]["action"] == "approve"
    assert not any(d["image_available"] for d in after["documents"])

    sms = client.get("/api/notifications", params={"application_id": app_id}).json()
    bodies = [n["body_en"] for n in sms]  # newest first
    assert "approved" in bodies[0]
    assert sum("needs a correction" in b for b in bodies) == 1
    assert all(n["to_masked"] == "98XXXXXX21" and n["body_ta"] for n in sms)

    # Decided applications are locked.
    assert client.patch(f"/api/applications/{app_id}", json={"action": "approve"}).status_code == 409


def test_needs_fix_sms_only_on_transition(client, monkeypatch):
    app_id = create(client)["id"]
    monkeypatch.setattr(documents_router, "validate_image", blurry_outcome)
    upload(client, app_id, "aadhaar_front")
    upload(client, app_id, "aadhaar_front")  # still blurry: stays needs_fix, no second SMS
    sms = client.get("/api/notifications", params={"application_id": app_id}).json()
    assert len(sms) == 1
    detail = client.get(f"/api/applications/{app_id}").json()
    assert detail["resubmissions"] == 1


def test_back_missing_blocks_only_after_id_proof_attempted(client, monkeypatch):
    def engine_consistency(docs):
        types = {d.declared_type for d in docs}
        missing = "aadhaar_front" in types and "aadhaar_back" not in types
        return ConsistencyResult(name_tier="not_enough_data",
                                 issues=[make_issue("AADHAAR_BACK_MISSING")] if missing else [])

    monkeypatch.setattr(ops_service, "check_consistency", engine_consistency)
    app_id = create(client)["id"]
    after_front = upload(client, app_id, "aadhaar_front")
    assert after_front["application"]["status"] == "submitted"
    assert after_front["consistency"]["issues"] == []
    after_pan = upload(client, app_id, "pan")
    assert after_pan["application"]["status"] == "needs_fix"
    assert "AADHAAR_BACK_MISSING" in after_pan["application"]["flag_codes"]
    sms = client.get("/api/notifications", params={"application_id": app_id}).json()
    assert "back side of the Aadhaar" in sms[0]["body_en"]
    after_back = upload(client, app_id, "aadhaar_back")
    assert after_back["application"]["status"] == "ready_for_officer"


def test_reject_requires_reason_and_uses_error_shape(client):
    app_id = create(client)["id"]
    res = client.patch(f"/api/applications/{app_id}", json={"action": "reject"})
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "REASON_REQUIRED"
    ok = client.patch(f"/api/applications/{app_id}", json={"action": "reject", "reason_code": "NAME_MISMATCH",
                                                           "note": "Different person"})
    assert ok.json()["status"] == "rejected"


def test_request_fix_sets_needs_fix_and_notifies(client):
    app_id = create(client)["id"]
    res = client.patch(f"/api/applications/{app_id}", json={"action": "request_fix", "reason_code": "GLARE"})
    assert res.json()["status"] == "needs_fix"
    sms = client.get("/api/notifications", params={"application_id": app_id}).json()
    assert "Light reflection" in sms[0]["body_en"]


def test_errors(client):
    assert client.get("/api/applications/app_nope").json()["error"]["code"] == "APPLICATION_NOT_FOUND"
    bad_office = client.post("/api/applications", json={"citizen_name": "X", "phone": "9876543210",
                                                        "service": "income_certificate", "office_id": "nope"})
    assert bad_office.status_code == 400
    bad_phone = client.post("/api/applications", json={"citizen_name": "X", "phone": "1234567890",
                                                       "service": "income_certificate", "office_id": "off_podanur_es"})
    assert bad_phone.json()["error"]["code"] == "INVALID_PHONE"
    app_id = create(client)["id"]
    res = client.post(f"/api/applications/{app_id}/documents", data={"declared_type": "passport"},
                      files={"file": ("card.jpg", jpeg(), "image/jpeg")})
    assert res.json()["error"]["code"] == "BAD_DECLARED_TYPE"
