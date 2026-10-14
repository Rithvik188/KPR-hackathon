"""Contract v1.4 on the ops side: stage chain VAO → RI → Tahsildar, service-specific supporting document, form check."""
import pytest
from fastapi.testclient import TestClient

import app.ops.routers.documents as documents_router
import app.ops.service as ops_service
from app.main import app
from app.ops.services import next_stage, required_slots_for, stage_sla_hours, supporting_type_for
from app.validation.messages import make_issue
from app.validation.types import ConsistencyResult

from tests.ops.test_applications_flow import accepted_outcome, create, jpeg


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(documents_router, "validate_image", accepted_outcome)
    monkeypatch.setattr(documents_router, "find_duplicates", lambda *a, **k: [])
    monkeypatch.setattr(ops_service, "check_consistency",
                        lambda docs, form=None: ConsistencyResult(name_tier="not_enough_data"))
    with TestClient(app) as c:
        yield c


def upload(client, app_id, declared):
    res = client.post(f"/api/applications/{app_id}/documents", data={"declared_type": declared},
                      files={"file": ("card.jpg", jpeg(), "image/jpeg")})
    assert res.status_code == 200, res.text
    return res.json()


def ready_application(client) -> str:
    app_id = create(client)["id"]
    for slot in ("aadhaar_front", "aadhaar_back", "pan", "parent_community_certificate"):
        last = upload(client, app_id, slot)
    assert last["application"]["status"] == "ready_for_officer"
    return app_id


def test_services_loader():
    assert supporting_type_for("community_certificate") == "parent_community_certificate"
    assert supporting_type_for("nativity_certificate") == "birth_certificate"
    assert supporting_type_for("income_certificate") == "income_proof"
    assert supporting_type_for("ration_card_update") == "address_proof"
    assert required_slots_for("income_certificate")[-1] == "supporting"
    assert next_stage("vao") == "ri" and next_stage("ri") == "tahsildar" and next_stage("tahsildar") is None
    assert (stage_sla_hours("vao"), stage_sla_hours("ri"), stage_sla_hours("tahsildar")) == (48, 24, 24)


def test_supporting_document_is_required_and_service_specific(client):
    app_id = create(client)["id"]
    for slot in ("aadhaar_front", "aadhaar_back", "pan"):
        last = upload(client, app_id, slot)
    assert last["application"]["status"] == "submitted"  # ID proofs alone are no longer enough
    wrong = client.post(f"/api/applications/{app_id}/documents", data={"declared_type": "birth_certificate"},
                        files={"file": ("p.jpg", jpeg(), "image/jpeg")})
    assert wrong.status_code == 400 and wrong.json()["error"]["code"] == "WRONG_SUPPORTING_DOCUMENT"
    done = upload(client, app_id, "parent_community_certificate")
    assert done["application"]["status"] == "ready_for_officer"
    assert done["application"]["stage"] == "vao"


def test_stage_chain_with_roles(client):
    app_id = ready_application(client)
    summary = client.get(f"/api/applications/{app_id}").json()
    assert summary["stage"] == "vao" and 47 < summary["stage_sla_hours_left"] <= 48

    # Wrong role, and non-final roles can't decide.
    assert client.patch(f"/api/applications/{app_id}", json={"action": "forward", "role": "ri"}).json()["error"]["code"] == "STAGE_MISMATCH"
    assert client.patch(f"/api/applications/{app_id}", json={"action": "approve", "role": "vao"}).status_code == 409

    ri = client.patch(f"/api/applications/{app_id}", json={"action": "forward", "role": "vao"}).json()
    assert ri["stage"] == "ri" and 23 < ri["stage_sla_hours_left"] <= 24
    taha = client.patch(f"/api/applications/{app_id}", json={"action": "forward", "role": "ri"}).json()
    assert taha["stage"] == "tahsildar"
    assert client.patch(f"/api/applications/{app_id}", json={"action": "forward", "role": "tahsildar"}).json()["error"]["code"] == "CANNOT_FORWARD"

    # ?stage= filter
    items = client.get("/api/applications", params={"stage": "tahsildar", "limit": 200}).json()["items"]
    assert app_id in [i["id"] for i in items]

    approved = client.patch(f"/api/applications/{app_id}", json={"action": "approve", "role": "tahsildar"}).json()
    assert approved["status"] == "approved" and approved["stage"] is None
    events = [h["event"] for h in client.get(f"/api/applications/{app_id}").json()["history"]]
    assert events.count("forwarded") == 2


def test_no_role_keeps_single_officer_behaviour(client):
    app_id = ready_application(client)
    res = client.patch(f"/api/applications/{app_id}", json={"action": "approve"})
    assert res.status_code == 200 and res.json()["status"] == "approved"


def test_request_fix_allowed_at_any_stage_and_clears_it(client):
    app_id = ready_application(client)
    res = client.patch(f"/api/applications/{app_id}", json={"action": "request_fix", "role": "vao", "reason_code": "BLUR"})
    assert res.status_code == 200
    assert res.json()["status"] == "needs_fix" and res.json()["stage"] is None


def test_form_check_is_passed_to_the_engine_and_blocks_on_mismatch(client, monkeypatch):
    seen = {}

    def engine(docs, form=None):
        seen["form"] = form
        return ConsistencyResult(name_tier="match", issues=[make_issue("FORM_DOB_MISMATCH")])

    monkeypatch.setattr(ops_service, "check_consistency", engine)
    res = client.post("/api/applications", json={"citizen_name": "Karthik R", "phone": "9876543221",
                                                  "service": "community_certificate", "office_id": "off_sulur_es2",
                                                  "citizen_dob": "1998-04-12"})
    assert res.status_code == 201 and res.json()["citizen_dob"] == "1998-04-12"
    app_id = res.json()["id"]
    out = None
    for slot in ("aadhaar_front", "aadhaar_back", "pan", "parent_community_certificate"):
        out = upload(client, app_id, slot)
    assert seen["form"] == {"name": "KARTHIK R", "dob": "1998-04-12"}
    assert out["application"]["status"] == "needs_fix"  # a blocking FORM_* issue holds it back
    assert "FORM_DOB_MISMATCH" in out["application"]["flag_codes"]
