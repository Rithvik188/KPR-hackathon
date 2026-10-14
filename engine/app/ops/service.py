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
from app.ops.services import next_stage, required_slots_for, stage_sla_hours
from app.ops.status import compute_app_status, effective_app_issues, latest_by_slot
from app.validation.api import check_consistency
from app.validation.types import ConsistencyResult, ExtractedDoc, Issue

SLA = timedelta(hours=72)
DECIDED = ("approved", "rejected")


def stage_fields(app: Application, ref) -> dict:
    """citizen_dob + the stage SLA fields (contract v1.4). `ref` is the time to measure stage_sla_hours_left from."""
    due = None
    left = None
    if app.stage and app.stage_entered_at is not None:
        due_dt = app.stage_entered_at + timedelta(hours=stage_sla_hours(app.stage))
        due = iso(due_dt)
        left = round((due_dt - ref).total_seconds() / 3600, 1)
    return {"citizen_dob": app.citizen_dob, "can_id": app.can_id, "stage": app.stage, "stage_due_at": due, "stage_sla_hours_left": left}


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
    """Re-run consistency on the latest document of each slot, cache it, and update the status and stage."""
    latest = latest_by_slot(docs)
    required = required_slots_for(app.service)
    extracted = [ExtractedDoc.from_dict(json.loads(d.extracted_json)) for d in latest.values() if d.extracted_json]
    # v1.4 form-vs-document check: the operator-typed name/DOB is what gets printed, so compare it too.
    form = {"name": app.citizen_name, "dob": app.citizen_dob}
    raw = check_consistency(extracted, form=form)
    consistency = raw.model_copy(update={"issues": effective_app_issues(raw.issues, set(latest), required)})
    app.consistency_json = consistency.model_dump_json()
    if app.status not in DECIDED:
        app.status = compute_app_status({slot: d.status for slot, d in latest.items()}, consistency.issues, required)
        _sync_stage(app)
    return consistency


def _sync_stage(app: Application) -> None:
    """Entering ready_for_officer starts the officer chain at VAO; leaving it clears the stage (contract v1.4)."""
    if app.status == "ready_for_officer":
        if app.stage is None:
            app.stage = "vao"
            app.stage_entered_at = now()
    elif app.status not in DECIDED:
        app.stage = None
        app.stage_entered_at = None


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
        resubmissions=app.resubmissions, **stage_fields(app, end))


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
    slot_order = (*required_slots_for(app.service), *(s for s in latest if s not in required_slots_for(app.service)))
    return ApplicationDetailOut(
        **summary(app, office_name, docs).model_dump(),
        documents=[_document_out(latest[s]) for s in slot_order if s in latest],
        consistency=consistency_of(app),
        history=[HistoryEventOut(at=iso(e.at), event=e.event, actor=e.actor, note=e.note) for e in events],
        decision=decision)
