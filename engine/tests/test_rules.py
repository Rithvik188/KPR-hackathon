import random

import pytest

from app.validation.rules import apply_rules, check_number, verhoeff_valid
from app.validation.text import correct_pattern, respace, to_digits
from datagen.numbers import make_aadhaar, make_invalid_aadhaar

rng = random.Random(7)
VALID = [make_aadhaar(rng) for _ in range(50)]


def test_generated_aadhaar_numbers_validate():
    assert all(verhoeff_valid(n) for n in VALID)


def test_every_single_digit_change_fails():
    for n in VALID[:10]:
        for i in range(12):
            for d in "0123456789":
                if d != n[i]:
                    assert not verhoeff_valid(n[:i] + d + n[i + 1:])


def test_every_adjacent_transposition_fails():
    for n in VALID[:20]:
        for i in range(11):
            if n[i] != n[i + 1]:
                assert not verhoeff_valid(n[:i] + n[i + 1] + n[i] + n[i + 2:])


def test_invalid_generator_is_invalid():
    assert not any(verhoeff_valid(make_invalid_aadhaar(rng)) for _ in range(50))


@pytest.mark.parametrize("number,code", [
    ("ABCPK1234F", None), ("ABCQK1234F", "INVALID_FORMAT"), ("ABCP1234F", "INVALID_FORMAT"),
    ("abcpk1234f", "INVALID_FORMAT"),
])
def test_pan(number, code):
    assert check_number("pan", number) == code


@pytest.mark.parametrize("number,code", [("ABC1234567", None), ("AB12345678", "INVALID_FORMAT"),
                                         ("ABC123456", "INVALID_FORMAT")])
def test_epic(number, code):
    assert check_number("voter_id", number) == code


def test_aadhaar_format_vs_checksum():
    assert check_number("aadhaar_front", "1" + VALID[0][1:]) == "INVALID_FORMAT"  # first digit 0/1
    assert check_number("aadhaar_front", VALID[0][:11]) == "INVALID_FORMAT"
    assert check_number("aadhaar_back", make_invalid_aadhaar(rng)) == "INVALID_CHECKSUM"


def test_confusables():
    assert to_digits("2O34 S6B7 89I2") == ("203456878912", 4)
    assert correct_pattern("ABCPK12B4F", "AAAAA9999A") == ("ABCPK1284F", 1)
    assert correct_pattern("A8CPK1234F", "AAAAA9999A") == ("ABCPK1234F", 1)


def test_respace_with_father_name():
    assert respace("KARTHIKRAJENDRAN", "RAJENDRAN") == "KARTHIK RAJENDRAN"
    assert respace("KARTHIKR", "RAJENDRAN") == "KARTHIK R"
    assert respace("R.KARTHIK", None) == "R. KARTHIK"


# ---- the confidence gate: "can't read" is never "invalid" ----

def test_gate_low_confidence_invalid_number_is_unreadable():
    bad = make_invalid_aadhaar(rng)
    rr = apply_rules("aadhaar_front", bad, 0.40, 0, min_conf=0.7)
    codes = [i.code for i in rr.issues]
    assert codes == ["UNREADABLE"]
    assert "INVALID_CHECKSUM" not in codes


def test_gate_missing_number_is_unreadable():
    assert [i.code for i in apply_rules("pan", None, None, 0, 0.7).issues] == ["UNREADABLE"]


def test_invalid_requires_second_read_agreement():
    bad = make_invalid_aadhaar(rng)
    agree = apply_rules("aadhaar_front", bad, 0.95, 0, 0.7, second_read=lambda: (bad, 0.9))
    assert [i.code for i in agree.issues] == ["INVALID_CHECKSUM"]
    other = bad[:-2] + ("0" if bad[-2] != "0" else "1") + bad[-1]
    disagree = apply_rules("aadhaar_front", bad, 0.95, 0, 0.7, second_read=lambda: (other, 0.9))
    assert [i.code for i in disagree.issues] == ["UNREADABLE"]
    failed = apply_rules("aadhaar_front", bad, 0.95, 0, 0.7, second_read=lambda: (None, None))
    assert [i.code for i in failed.issues] == ["UNREADABLE"]


def test_second_read_can_rescue_a_misread_valid_card():
    good = VALID[3]
    misread = good[:5] + ("8" if good[5] != "8" else "6") + good[6:]
    rr = apply_rules("aadhaar_front", misread, 0.9, 0, 0.7, second_read=lambda: (good, 0.9))
    assert rr.trusted and rr.number == good
    assert [i.code for i in rr.issues] == ["OCR_AUTOCORRECTED"]


def test_autocorrect_flagged():
    rr = apply_rules("aadhaar_front", VALID[0], 0.9, 2, 0.7)
    assert rr.trusted and [i.code for i in rr.issues] == ["OCR_AUTOCORRECTED"]
