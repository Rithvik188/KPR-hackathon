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
