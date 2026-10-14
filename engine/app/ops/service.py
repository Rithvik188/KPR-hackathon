"""Application read/write helpers shared by the ops routers: slots, consistency, status and serialisation."""
import json
from datetime import timedelta
from pathlib import Path

from sqlmodel import Session, select

from app.core.errors import api_error
from app.core.models import AppEvent, Application, Document, iso, new_id
from app.ops.clock import now
from app.ops.schemas import (ApplicationDetailOut, ApplicationSummaryOut, DecisionOut, DocumentOut,
                             HistoryEventOut)
from app.ops.status import REQUIRED_SLOTS, compute_app_status, effective_app_issues, latest_by_slot
from app.validation.api import check_consistency
from app.validation.types import ConsistencyResult, ExtractedDoc, Issue

SLA = timedelta(hours=72)
DECIDED = ("approved", "rejected")


def get_app(session: Session, app_id: str) -> Application:
    app = session.get(Application, app_id)
    if app is None:
        raise api_error(404, "APPLICATION_NOT_FOUND", f"No application {app_id}")
    return app


def documents_of(session: Session, app_id: str) -> list[Document]:
    """All uploads of an application, oldest first."""
    q = select(Document).where(Document.application_id == app_id).order_by(Document.uploaded_at, Document.id)
    return list(session.exec(q).all())


def documents_by_app(session: Session, app_ids: list[str]) -> dict[str, list[Document]]:
    out: dict[str, list[Document]] = {a: [] for a in app_ids}
    if not app_ids:
        return out
    q = select(Document).where(Document.application_id.in_(app_ids)).order_by(Document.uploaded_at, Document.id)
    for doc in session.exec(q).all():
        out[doc.application_id].append(doc)
    return out


def issues_of(doc: Document) -> list[Issue]:
    return [Issue.model_validate(i) for i in json.loads(doc.issues_json or "[]")]


def consistency_of(app: Application) -> ConsistencyResult:
    if app.consistency_json:
        return ConsistencyResult.model_validate_json(app.consistency_json)
    return ConsistencyResult(name_tier="not_enough_data")


def add_event(session: Session, app_id: str, event: str, actor: str, note: str | None = None) -> None:
    session.add(AppEvent(id=new_id("ev"), application_id=app_id, at=now(), event=event, actor=actor, note=note))


def recompute(app: Application, docs: list[Document]) -> ConsistencyResult:
    """Re-run consistency on the latest document of each slot, cache it, and update the status."""
    latest = latest_by_slot(docs)
    extracted = [ExtractedDoc.from_dict(json.loads(d.extracted_json)) for d in latest.values() if d.extracted_json]
    raw = check_consistency(extracted)
    consistency = raw.model_copy(update={"issues": effective_app_issues(raw.issues, set(latest))})
    app.consistency_json = consistency.model_dump_json()
    if app.status not in DECIDED:
        app.status = compute_app_status({slot: d.status for slot, d in latest.items()}, consistency.issues)
    return consistency


def blocking_issues(docs: list[Document], consistency: ConsistencyResult) -> list[Issue]:
    """Blocking issues on the latest documents plus application-level ones (for the needs_fix SMS)."""
    issues = [i for d in latest_by_slot(docs).values() for i in issues_of(d)] + list(consistency.issues)
    return [i for i in issues if i.severity == "blocking"]


def _flag_codes(latest: list[Document], consistency: ConsistencyResult) -> list[str]:
    codes = [i.code for d in latest for i in issues_of(d) if i.severity != "info"]
    codes += [i.code for i in consistency.issues if i.severity != "info"]
    return list(dict.fromkeys(codes))


def summary(app: Application, office_name: str, docs: list[Document]) -> ApplicationSummaryOut:
    latest = list(latest_by_slot(docs).values())
    end = app.decided_at or now()
    return ApplicationSummaryOut(
        id=app.id, citizen_name=app.citizen_name, phone_masked=app.phone_masked, service=app.service,
        office_id=app.office_id, office_name=office_name, status=app.status,  # type: ignore[arg-type]
        created_at=iso(app.created_at), updated_at=iso(app.updated_at), sla_due_at=iso(app.sla_due_at),
        sla_hours_left=round((app.sla_due_at - end).total_seconds() / 3600, 1),
        flag_codes=_flag_codes(latest, consistency_of(app)), doc_count=len(latest),
        resubmissions=app.resubmissions)


def _document_out(doc: Document) -> DocumentOut:
    return DocumentOut(id=doc.id, doc_type=doc.doc_type, declared_type=doc.declared_type, status=doc.status,
                       issues=issues_of(doc),
                       fields=json.loads(doc.fields_json) if doc.fields_json else None,
                       uploaded_at=iso(doc.uploaded_at),
                       image_available=bool(doc.image_path) and Path(doc.image_path).exists())


def detail(session: Session, app: Application, office_name: str) -> ApplicationDetailOut:
    docs = documents_of(session, app.id)
    latest = latest_by_slot(docs)
    events = session.exec(select(AppEvent).where(AppEvent.application_id == app.id)
                          .order_by(AppEvent.at, AppEvent.id)).all()
    decision = None
    if app.decision_action in ("approve", "reject") and app.decided_at:
        decision = DecisionOut(action=app.decision_action, reason_code=app.decision_reason,  # type: ignore[arg-type]
                               note=app.decision_note, at=iso(app.decided_at))
    return ApplicationDetailOut(
        **summary(app, office_name, docs).model_dump(),
        documents=[_document_out(latest[s]) for s in REQUIRED_SLOTS if s in latest],
        consistency=consistency_of(app),
        history=[HistoryEventOut(at=iso(e.at), event=e.event, actor=e.actor, note=e.note) for e in events],
        decision=decision)
