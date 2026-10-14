from fastapi.testclient import TestClient

from app.main import app


def test_offices_inserted_on_startup_and_listed():
    with TestClient(app) as client:  # runs the lifespan: create_db() then ops startup()
        res = client.get("/api/offices")
    assert res.status_code == 200
    offices = res.json()
    assert len(offices) == 18
    assert set(offices[0]) == {"id", "name", "type", "taluk", "lat", "lng"}
    sulur2 = next(o for o in offices if o["id"] == "off_sulur_es2")
    assert sulur2["type"] == "esevai_centre" and sulur2["taluk"] == "Sulur"


def test_startup_is_idempotent():
    with TestClient(app) as client:
        pass
    with TestClient(app) as client:
        assert len(client.get("/api/offices").json()) == 18
