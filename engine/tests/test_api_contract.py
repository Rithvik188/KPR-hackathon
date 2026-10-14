"""HTTP-level contract checks for Person 1 endpoints."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def _jpeg(w=64, h=40) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (200, 200, 200)).save(buf, "JPEG")
    return buf.getvalue()


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and body["version"] == "1.4"


def test_validate_rejects_non_image_as_result(client):
    r = client.post("/api/validate", files={"file": ("x.jpg", b"%PDF-1.4 not an image", "image/jpeg")})
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "fixable"
    assert body["issues"][0]["code"] == "UNSUPPORTED_FILE"
    assert body["issues"][0]["msg_ta"]


def test_validate_too_large_is_result(client):
    big = b"\xff\xd8\xff" + b"0" * (10 * 1024 * 1024 + 10)
    r = client.post("/api/validate", files={"file": ("big.jpg", big, "image/jpeg")})
    assert r.status_code == 200
    assert r.json()["issues"][0]["code"] == "FILE_TOO_LARGE"


def test_validate_bad_declared_type_is_error_shape(client):
    r = client.post("/api/validate", files={"file": ("a.jpg", _jpeg(), "image/jpeg")}, data={"declared_type": "passport"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "BAD_DECLARED_TYPE"


def test_validate_shape(client):
    r = client.post("/api/validate", files={"file": ("a.jpg", _jpeg(), "image/jpeg")}, data={"declared_type": "pan"})
    assert r.status_code == 200
    body = r.json()
    assert set(body) == {"document_id", "doc_type", "declared_type", "status", "issues", "quality", "fields", "ocr",
                         "timings_ms"}
    assert body["status"] in {"accepted", "fixable", "invalid"}
    assert set(body["timings_ms"]) == {"quality", "ocr", "total"}


def test_metrics_detection_has_source(client):
    body = client.get("/api/metrics/detection").json()
    assert body["source"] in {"evaluation", "FIXTURE"}


def test_unknown_api_route_is_error_shape(client):
    r = client.get("/api/does-not-exist")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
