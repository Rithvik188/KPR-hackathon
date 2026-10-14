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
