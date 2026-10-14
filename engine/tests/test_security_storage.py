import re

import pytest

from app.core.security import aadhaar_hmac, mask_aadhaar, mask_phone
from app.core.storage import delete_image, load_image, save_image


def test_hmac_is_keyed_and_stable():
    h = aadhaar_hmac("2345 6789 0124")
    assert h == aadhaar_hmac("234567890124")
    assert len(h) == 64 and "234567890124" not in h
    import hashlib
    assert h != hashlib.sha256(b"234567890124").hexdigest()  # not a plain hash


def test_hmac_rejects_wrong_length():
    with pytest.raises(ValueError):
        aadhaar_hmac("1234")


@pytest.mark.parametrize("raw", ["234567890124", "2345 6789 0124", "2345-6789-0124", "12", "", "99999999999999"])
def test_mask_never_leaks_more_than_4_digits(raw):
    m = mask_aadhaar(raw)
    assert len(re.sub(r"\D", "", m)) <= 4
    assert m.startswith("XXXX XXXX ")


def test_mask_phone():
    assert mask_phone("9876543221") == "98XXXXXX21"
    assert mask_phone("+91 98765 43221") == "98XXXXXX21"


def test_storage_roundtrip_encrypted():
    data = b"\xff\xd8\xff fake jpeg bytes"
    path = save_image("doc_test1", data)
    with open(path, "rb") as f:
        assert data not in f.read()  # encrypted at rest
    assert load_image("doc_test1") == data
    delete_image("doc_test1")
    assert load_image("doc_test1") is None


def test_storage_rejects_path_traversal():
    with pytest.raises(ValueError):
        save_image("../evil", b"x")
    assert load_image("../evil") is None
