"""Aadhaar privacy helpers. Never log, return or store a full Aadhaar number."""
import hashlib
import hmac
import re

from app.core.config import get_settings

_NON_DIGIT = re.compile(r"\D")


def _digits(value: str) -> str:
    return _NON_DIGIT.sub("", value or "")


def aadhaar_hmac(digits: str) -> str:
    """Keyed HMAC-SHA256 (hex). A plain hash of 10^12 numbers would be brute-forceable."""
    d = _digits(digits)
    if len(d) != 12:
        raise ValueError("aadhaar_hmac expects exactly 12 digits")
    key = get_settings().aadhaar_hmac_secret.encode()
    return hmac.new(key, d.encode(), hashlib.sha256).hexdigest()


def mask_aadhaar(digits: str) -> str:
    """'XXXX XXXX 1234'. Shows at most the last 4 digits whatever the input length."""
    d = _digits(digits)
    return f"XXXX XXXX {d[-4:]}" if len(d) >= 4 else "XXXX XXXX XXXX"


def mask_phone(phone: str) -> str:
    """'9876543221' -> '98XXXXXX21'."""
    d = _digits(phone)
    if len(d) > 10:
        d = d[-10:]  # drop +91 / leading 0
    if len(d) < 4:
        return "X" * len(d)
    return d[:2] + "X" * (len(d) - 4) + d[-2:]
