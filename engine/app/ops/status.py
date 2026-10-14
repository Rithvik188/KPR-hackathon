"""AppStatus rule (contract §1, v1.1/v1.4). Pure functions, so they're easy to test without a database.

Slots are keyed by the operator's declared type. PAN and Voter ID share one "id_proof" slot; the service's
supporting document (v1.4) shares one "supporting" slot. The most recent upload into a slot is the one that counts.
"""
from collections.abc import Iterable
from typing import Protocol

from app.ops.services import SUPPORTING_SLOT, services_data
from app.validation.types import Issue

Slot = str
# The ID-proof slots, always required; a service adds its "supporting" slot (v1.4).
ID_SLOTS: tuple[Slot, ...] = ("aadhaar_front", "aadhaar_back", "id_proof")
BACK_MISSING = "AADHAAR_BACK_MISSING"


class DocLike(Protocol):
    declared_type: str | None
    doc_type: str
    status: str


def slot_of(declared_type: str | None) -> Slot | None:
    if declared_type in ("pan", "voter_id"):
        return "id_proof"
    if declared_type in ("aadhaar_front", "aadhaar_back"):
        return declared_type
    if declared_type in services_data()["supporting_types"]:
        return SUPPORTING_SLOT
    return None


def latest_by_slot[D: DocLike](docs_oldest_first: Iterable[D]) -> dict[Slot, D]:
    """Latest document per slot. Pass documents ordered by upload time, oldest first."""
    latest: dict[Slot, D] = {}
    for doc in docs_oldest_first:
        slot = slot_of(doc.declared_type or doc.doc_type)
        if slot is not None:
            latest[slot] = doc
    return latest


def effective_app_issues(app_issues: Iterable[Issue], attempted: set[Slot],
                         required_slots: tuple[Slot, ...] = ID_SLOTS, finished: bool = False) -> list[Issue]:
    """Application-level issues that apply right now.

    AADHAAR_BACK_MISSING only counts once every other required slot has been attempted (or the operator
    finished), and never once the back slot itself has an upload, even one that failed quality. Other
    application-level issues (FORM_*, NAME_*, DOB_*) always apply.
    """
    out = []
    for issue in app_issues:
        if issue.code == BACK_MISSING:
            if "aadhaar_back" in attempted:
                continue
            others_attempted = all(s in attempted for s in required_slots if s != "aadhaar_back")
            if not (others_attempted or finished):
                continue
        out.append(issue)
    return out


def compute_app_status(latest_statuses: dict[Slot, str], app_issues: Iterable[Issue],
                       required_slots: tuple[Slot, ...] = ID_SLOTS) -> str:
    """`latest_statuses` maps slot -> DocStatus of its latest upload; `app_issues` are the effective ones."""
    blocking_app_issue = any(i.severity == "blocking" for i in app_issues)
    if blocking_app_issue or any(s in ("fixable", "invalid") for s in latest_statuses.values()):
        return "needs_fix"
    if all(latest_statuses.get(slot) == "accepted" for slot in required_slots):
        return "ready_for_officer"
    return "submitted"
