"""Contract v1.4: form-vs-document check and supporting documents."""
from pathlib import Path

import pytest

from app.validation.api import validate_image
from app.validation.consistency import check_consistency
from app.validation.types import ExtractedDoc
from datagen.generate_demo import DEMO_DIR


def doc(slot, name=None, dob=None):
    return ExtractedDoc(doc_type=slot, declared_type=slot, name=name, dob=dob)


DOCS = [doc("aadhaar_front", "R. KARTHIK", "1998-04-12"), doc("aadhaar_back"),
        doc("pan", "KARTHIK RAJENDRAN", "1998-04-12")]


def codes(r):
    return [i.code for i in r.issues]


def test_form_reordered_initial_is_a_match():
    r = check_consistency(DOCS, form={"name": "KARTHIK R", "dob": "1998-04-12"})
    assert r.form_check["name_tier"] == "match" and r.form_check["dob_match"] is True
    assert not [c for c in codes(r) if c.startswith("FORM_")]


def test_form_full_name_is_variant_for_officer():
    r = check_consistency(DOCS, form={"name": "KARTHIK RAJENDRAN", "dob": "1998-04-12"})
    assert r.form_check["name_tier"] == "likely_match"
    assert "FORM_NAME_VARIANT" in codes(r)


def test_form_typo_name_is_blocking():
    r = check_consistency(DOCS, form={"name": "KARTHICK RAMESH", "dob": "1998-04-12"})
    assert "FORM_NAME_MISMATCH" in codes(r)
    issue = next(i for i in r.issues if i.code == "FORM_NAME_MISMATCH")
    assert issue.severity == "blocking" and issue.audience == "citizen" and issue.msg_ta


def test_form_wrong_dob_is_blocking():
    r = check_consistency(DOCS, form={"name": "KARTHIK R", "dob": "1998-12-04"})
    assert "FORM_DOB_MISMATCH" in codes(r)


def test_no_form_keeps_old_behaviour():
    r = check_consistency(DOCS)
    assert r.form_check is None and r.name_tier == "likely_match"


def test_form_check_works_with_one_document():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12")], form={"name": "SURESH K"})
    assert r.name_tier == "not_enough_data" and "FORM_NAME_MISMATCH" in codes(r)


IMG = sorted(DEMO_DIR.glob("*.jpg"))


@pytest.mark.skipif(not IMG, reason="demo images not generated")
def test_aadhaar_in_birth_certificate_slot_is_wrong_type():
    r = validate_image((DEMO_DIR / "02_aadhaar_front_clean.jpg").read_bytes(), "birth_certificate").result
    assert r.status == "fixable" and "WRONG_DOC_TYPE" in codes(r)


@pytest.mark.skipif(not IMG, reason="demo images not generated")
def test_supporting_document_shape():
    out = validate_image((DEMO_DIR / "11_birth_certificate.jpg").read_bytes(), "birth_certificate")
    r = out.result
    assert r.status == "accepted" and r.doc_type == "birth_certificate"
    assert "CONTENT_NOT_VERIFIED" in codes(r) and set(r.fields) == {"title"}
    assert out.extracted is None and out.aadhaar_hmac is None and out.card_jpeg


def test_blurry_page_skips_ocr():
    r = validate_image(Path(DEMO_DIR / "13_birth_certificate_blurry.jpg").read_bytes(), "birth_certificate").result
    assert r.status == "fixable" and "BLUR" in codes(r) and r.ocr is None


@pytest.mark.skipif(not IMG, reason="demo images not generated")
def test_eaadhaar_letter_fills_both_slots_without_the_vid():
    data = (DEMO_DIR / "15_eaadhaar_letter.jpg").read_bytes()
    front = validate_image(data, "aadhaar_front")
    back = validate_image(data, "aadhaar_back")
    for out, slot in ((front, "aadhaar_front"), (back, "aadhaar_back")):
        r = out.result
        assert r.status == "accepted" and r.doc_type == slot and "EAADHAAR_PAGE" in codes(r)
        assert r.fields["id_number_display"].startswith("XXXX XXXX ")
    assert front.aadhaar_hmac == back.aadhaar_hmac  # same person, same number on both
    front_card = validate_image((DEMO_DIR / "02_aadhaar_front_clean.jpg").read_bytes(), "aadhaar_front")
    assert front.aadhaar_hmac == front_card.aadhaar_hmac  # the letter belongs to the demo citizen
    assert front.result.fields["dob"] == "1998-04-12"


def test_wrong_length_number_is_unreadable_not_invalid():
    from app.validation.rules import apply_rules
    rr = apply_rules("aadhaar_front", "23456789012", 0.95, 0, 0.7)  # 11 digits read
    assert [i.code for i in rr.issues] == ["UNREADABLE"]
