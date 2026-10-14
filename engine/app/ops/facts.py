"""Per-application facts for analytics (alerts and operations metrics), loaded in two cheap queries.

An application's `codes` are every blocking issue code it ever had: on any uploaded document (including the
first, failed attempt of a slot that was later fixed) and in its cached application-level consistency result.
An application with no codes was "first time right".
"""
import json
from dataclasses import dataclass, field
from datetime import datetime

from sqlmodel import Session, select

from app.core.models import Application, Document


@dataclass
class AppFacts:
    id: str
    office_id: str
    status: str
    created_at: datetime
    decided_at: datetime | None
    decision_action: str | None
    sla_due_at: datetime
    resubmissions: int
    is_seed: bool
    codes: set[str] = field(default_factory=set)

    @property
    def decided(self) -> bool:
        return self.status in ("approved", "rejected")

    def open_at(self, t: datetime) -> bool:
        """Undecided at time t (part of the backlog)."""
        return self.created_at <= t and (self.decided_at is None or self.decided_at > t)


def _blocking_codes(issues_json: str | None) -> set[str]:
    return {i["code"] for i in json.loads(issues_json or "[]") if i.get("severity") == "blocking"}


def load_facts(session: Session, since: datetime | None = None) -> list[AppFacts]:
    """Applications created at or after `since` (all if None), with their blocking issue codes."""
    q = select(Application)
    if since is not None:
        q = q.where(Application.created_at >= since)
    facts = {a.id: AppFacts(id=a.id, office_id=a.office_id, status=a.status, created_at=a.created_at,
                            decided_at=a.decided_at, decision_action=a.decision_action, sla_due_at=a.sla_due_at,
                            resubmissions=a.resubmissions, is_seed=a.is_seed,
                            codes=_blocking_codes(_consistency_issues(a.consistency_json)))
             for a in session.exec(q).all()}

    dq = select(Document.application_id, Document.issues_json).where(Document.issues_json != "[]")
    if since is not None:
        dq = dq.where(Document.uploaded_at >= since)  # documents are always uploaded after their application
    for app_id, issues_json in session.exec(dq).all():
        if app_id in facts:
            facts[app_id].codes |= _blocking_codes(issues_json)
    return list(facts.values())


def _consistency_issues(consistency_json: str | None) -> str:
    if not consistency_json:
        return "[]"
    return json.dumps(json.loads(consistency_json).get("issues", []))
