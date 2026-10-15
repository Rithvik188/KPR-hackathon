"""Test env: throwaway secrets and data dir, set before any app module is imported."""
import os
import tempfile

_tmp = tempfile.mkdtemp(prefix="sevaicheck_test_")
os.environ.setdefault("AADHAAR_HMAC_SECRET", "t" * 64)
os.environ.setdefault("IMAGE_ENC_KEY", "dGVzdC1rZXktdGVzdC1rZXktdGVzdC1rZXktMTIzNDU=")
os.environ["DATA_DIR"] = _tmp
os.environ["DATABASE_URL"] = ""
os.environ.setdefault("OCR_WARMUP", "0")
os.environ["SERVE_WEB"] = "0"
os.environ["AUTH_REQUIRED"] = "0"  # tests/test_security.py turns enforcement on explicitly
os.environ["STAFF_DEMO_PASSWORD"] = "test-staff-password-123"
os.environ["DEMO_OTP_IN_RESPONSE"] = "1"


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_rate_limits():
    """All tests share one client IP; start each with empty rate-limit windows."""
    from app.core import auth

    auth._hits.clear()
    yield
