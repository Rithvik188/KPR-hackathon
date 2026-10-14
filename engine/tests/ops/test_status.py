"""AppStatus rule (contract §1, v1.1): pure-function tests, no database."""
from dataclasses import dataclass

from app.ops.status import compute_app_status, effective_app_issues, latest_by_slot, slot_of
from app.validation.messages import make_issue

ALL_ACCEPTED = {"aadhaar_front": "accepted", "aadhaar_back": "accepted", "id_proof": "accepted"}


@dataclass
class Doc:
    declared_type: str | None
    doc_type: str
    status: str


def test_all_required_accepted_is_ready_for_officer():
    assert compute_app_status(ALL_ACCEPTED, []) == "ready_for_officer"


def test_still_collecting_is_submitted():
    assert compute_app_status({"aadhaar_front": "accepted"}, []) == "submitted"
    assert compute_app_status({}, []) == "submitted"


def test_any_fixable_or_invalid_latest_doc_needs_fix():
    assert compute_app_status({"aadhaar_front": "fixable"}, []) == "needs_fix"
    assert compute_app_status({**ALL_ACCEPTED, "id_proof": "invalid"}, []) == "needs_fix"


def test_blocking_app_issue_needs_fix_but_warning_does_not():
    assert compute_app_status(ALL_ACCEPTED, [make_issue("NAME_MISMATCH")]) == "needs_fix"
    assert compute_app_status(ALL_ACCEPTED, [make_issue("NAME_LIKELY_MATCH")]) == "ready_for_officer"


def test_slots_use_declared_type_even_when_detection_says_unknown():
    blurry = Doc("aadhaar_front", "unknown", "fixable")
    retake = Doc("aadhaar_front", "aadhaar_front", "accepted")
    assert latest_by_slot([blurry])["aadhaar_front"] is blurry
    assert latest_by_slot([blurry, retake])["aadhaar_front"] is retake


def test_pan_and_voter_share_the_id_proof_slot_latest_wins():
    pan = Doc("pan", "pan", "fixable")
    voter = Doc("voter_id", "voter_id", "accepted")
    latest = latest_by_slot([pan, voter])
    assert latest["id_proof"] is voter
    assert slot_of("pan") == slot_of("voter_id") == "id_proof"


def test_back_missing_ignored_until_other_slots_attempted():
    back_missing = [make_issue("AADHAAR_BACK_MISSING")]
    # Only the front is in: keep collecting, no SMS.
    assert effective_app_issues(back_missing, {"aadhaar_front"}) == []
    statuses = {"aadhaar_front": "accepted"}
    assert compute_app_status(statuses, effective_app_issues(back_missing, set(statuses))) == "submitted"
    # Front and ID proof attempted, back still absent: now it blocks.
    attempted = {"aadhaar_front", "id_proof"}
    assert [i.code for i in effective_app_issues(back_missing, attempted)] == ["AADHAAR_BACK_MISSING"]
    statuses = {"aadhaar_front": "accepted", "id_proof": "accepted"}
    assert compute_app_status(statuses, effective_app_issues(back_missing, attempted)) == "needs_fix"
    # The operator pressed Finish.
    assert effective_app_issues(back_missing, {"aadhaar_front"}, finished=True)


def test_back_missing_dropped_once_back_slot_has_any_upload():
    back_missing = [make_issue("AADHAAR_BACK_MISSING")]
    assert effective_app_issues(back_missing, {"aadhaar_front", "aadhaar_back", "id_proof"}) == []
