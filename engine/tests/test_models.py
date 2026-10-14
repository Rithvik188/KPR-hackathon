"""Rows with default timestamps must insert (sqlmodel 0.0.48 rejects naive datetimes)."""
from datetime import timedelta

from sqlmodel import Session, select

from app.core.db import create_db, engine
from app.core.models import AppEvent, Application, Document, Office, iso, utcnow
from app.validation.duplicates import find_duplicates


def test_insert_and_read_timestamps_and_duplicates(monkeypatch):
    create_db()
    with Session(engine) as s:
        s.merge(Office(id="off_m", name="m", type="taluk_office", taluk="m", lat=0, lng=0))
        for app_id in ("app_m1", "app_m2"):
            s.merge(Application(id=app_id, citizen_name="x", phone_masked="98XXXXXX21", service="income_certificate",
                                office_id="off_m", status="submitted", sla_due_at=utcnow() + timedelta(hours=72)))
        s.merge(Document(id="doc_m1", application_id="app_m1", doc_type="aadhaar_front", status="accepted",
                         aadhaar_hmac="ab" * 32, phash="ff00ff00ff00ff00"))
        s.merge(Document(id="doc_m2", application_id="app_m2", doc_type="pan", status="accepted",
                         phash="0f0f0f0f0f0f0f0f"))
        s.merge(AppEvent(id="ev_m", application_id="app_m1", event="application_created", actor="operator"))
        s.commit()
        app = s.exec(select(Application).where(Application.id == "app_m1")).one()
        assert iso(app.created_at).endswith("Z")
        assert find_duplicates(s, "ab" * 32, None, "app_m2") == ["app_m1"]
        assert find_duplicates(s, "ab" * 32, None, "app_m1") == []
        import app.validation.duplicates as dup
        monkeypatch.setattr(dup, "get_thresholds", lambda: {"phash_max_distance": 4})
        assert find_duplicates(s, None, "ff00ff00ff00ff00", "app_x") == ["app_m1"]  # identical photo
        monkeypatch.setattr(dup, "get_thresholds", lambda: {"phash_max_distance": -1})  # tuned: disabled
        assert find_duplicates(s, None, "ff00ff00ff00ff00", "app_x") == []


def test_citizen_can_profile_and_phone_hmac():
    import pytest
    from app.core.models import Citizen
    from app.core.security import phone_hmac

    create_db()
    h = phone_hmac("+91 98765 43221")
    assert h == phone_hmac("9876543221") and "9876543221" not in h and len(h) == 64
    with pytest.raises(ValueError):
        phone_hmac("12345")
    with Session(engine) as s:
        s.merge(Citizen(id="CAN2026000001", name="KARTHIK R", dob="1998-04-12", phone_hmac=h,
                        phone_masked="98XXXXXX21", pin_code="641402"))
        s.merge(Office(id="off_c", name="c", type="esevai_centre_private", taluk="c", lat=0, lng=0))
        s.merge(Application(id="app_c", citizen_name="KARTHIK R", citizen_dob="1998-04-12", can_id="CAN2026000001",
                            phone_masked="98XXXXXX21", service="income_certificate", office_id="off_c",
                            status="submitted", sla_due_at=utcnow()))
        s.commit()
        c = s.exec(select(Citizen).where(Citizen.phone_hmac == h)).one()
        assert c.id == "CAN2026000001"
        assert s.get(Application, "app_c").can_id == c.id
