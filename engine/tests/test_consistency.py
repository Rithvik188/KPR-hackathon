from app.validation.consistency import check_consistency, compare_names, normalize_name
from app.validation.types import ExtractedDoc


def doc(slot, name=None, dob=None):
    return ExtractedDoc(doc_type=slot, declared_type=slot, name=name, dob=dob)


def codes(res):
    return [i.code for i in res.issues]


def test_normalize_strips_relation_and_punctuation():
    assert normalize_name("S/O R. Karthik") == ["R", "KARTHIK"]


def test_initials_same_dob_is_likely_match():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12"), doc("aadhaar_back"),
                           doc("pan", "KARTHIK RAJENDRAN", "1998-04-12")])
    assert r.name_tier == "likely_match"
    likely = next(i for i in r.issues if i.code == "NAME_LIKELY_MATCH")
    assert likely.evidence["initial_expanded"] == "R→RAJENDRAN"
    assert likely.severity == "warning" and likely.audience == "officer"
    assert r.dob_match is True


def test_initials_survive_lost_spaces():
    tier, _, ev = compare_names("R.KARTHIK", "KARTHIKRAJENDRAN", True)
    assert tier == "likely_match" and ev["initial_expanded"] == "R→RAJENDRAN"
    tier, _, ev = compare_names("KARTHIK R", "KARTHIKRAJENDRAN", True)
    assert tier == "likely_match"


def test_other_father_different_dob_is_mismatch():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12"), doc("aadhaar_back"),
                           doc("pan", "KARTHIK RAMESH", "1995-09-03")])
    assert r.name_tier == "mismatch"
    assert "NAME_MISMATCH" in codes(r) and "DOB_MISMATCH" in codes(r)


def test_identical_names_match():
    r = check_consistency([doc("aadhaar_front", "KARTHIK RAJENDRAN", "1998-04-12"), doc("aadhaar_back"),
                           doc("pan", "KARTHIK RAJENDRAN", "1998-04-12")])
    assert r.name_tier == "match" and codes(r) == []


def test_initial_based_is_never_full_match():
    tier, _, _ = compare_names("R. KARTHIK", "KARTHIK RAJENDRAN", True)
    assert tier != "match"


def test_different_given_name_is_mismatch():
    tier, _, _ = compare_names("SURESH RAJENDRAN", "KARTHIK RAJENDRAN", True)
    assert tier == "mismatch"


def test_back_missing():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12"),
                           doc("pan", "KARTHIK RAJENDRAN", "1998-04-12")])
    assert "AADHAAR_BACK_MISSING" in codes(r)


def test_not_enough_data():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12")])
    assert r.name_tier == "not_enough_data"


def test_worst_pair_is_reported():
    r = check_consistency([doc("aadhaar_front", "R. KARTHIK", "1998-04-12"), doc("aadhaar_back"),
                           doc("pan", "KARTHIK RAJENDRAN", "1998-04-12"),
                           doc("voter_id", "MEENA S", "1998-04-12")])
    assert r.name_tier == "mismatch"
