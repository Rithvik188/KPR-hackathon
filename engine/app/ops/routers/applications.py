"""POST/GET /applications, GET /applications/{id} and the officer PATCH (approve, reject, request_fix)."""
import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy import case, func
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.errors import api_error
from app.core.models import Application, Office, new_id
from app.ops.clock import now as utc_now
from app.core.security import mask_phone
from app.core.storage import delete_image
from app.ops.notifications import notify_decision
from app.ops.offices import office_names
from app.ops.schemas import (ApplicationDetailOut, ApplicationListOut, ApplicationSummaryOut, AppStatus,
                             CreateApplicationIn, OfficerActionIn, Stage)
from app.ops.services import next_stage
from app.ops.service import DECIDED, SLA, add_event, detail, documents_by_app, documents_of, get_app, summary

router = APIRouter(tags=["ops"])

_PHONE = re.compile(r"^[6-9]\d{9}$")


@router.post("/applications", status_code=201, response_model=ApplicationSummaryOut)
def create_application(body: CreateApplicationIn, session: Session = Depends(get_session)) -> ApplicationSummaryOut:
    office = session.get(Office, body.office_id)
    if office is None:
        raise api_error(400, "UNKNOWN_OFFICE", f"No office {body.office_id}")
    digits = re.sub(r"\D", "", body.phone)[-10:]
    if not _PHONE.match(digits):
        raise api_error(422, "INVALID_PHONE", "Enter a 10-digit mobile number starting with 6, 7, 8 or 9")
    now = utc_now()
    app = Application(id=new_id("app"), citizen_name=" ".join(body.citizen_name.split()).upper(),
                      citizen_dob=(body.citizen_dob or None), phone_masked=mask_phone(digits), service=body.service,
                      office_id=office.id, status="submitted", created_at=now, updated_at=now, sla_due_at=now + SLA)
    session.add(app)
    add_event(session, app.id, "application_created", "operator")
    session.commit()
    session.refresh(app)
    return summary(app, office.name, [])


@router.get("/applications", response_model=ApplicationListOut)
def list_applications(status: AppStatus | None = None, office_id: str | None = None, stage: Stage | None = None,
                      limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
                      session: Session = Depends(get_session)) -> ApplicationListOut:
    q = select(Application)
    count_q = select(func.count()).select_from(Application)
    if status:
        q = q.where(Application.status == status)
        count_q = count_q.where(Application.status == status)
    if office_id:
        q = q.where(Application.office_id == office_id)
        count_q = count_q.where(Application.office_id == office_id)
    if stage:
        q = q.where(Application.stage == stage)
        count_q = count_q.where(Application.stage == stage)
    # Contract: ready_for_officer first, then by sla_hours_left ascending (= earliest SLA due date first).
    ready_first = case((Application.status == "ready_for_officer", 0), else_=1)
    apps = session.exec(q.order_by(ready_first, Application.sla_due_at, Application.id)
                        .offset(offset).limit(limit)).all()
    docs = documents_by_app(session, [a.id for a in apps])
    names = office_names(session)
    return ApplicationListOut(items=[summary(a, names.get(a.office_id, a.office_id), docs[a.id]) for a in apps],
                              total=session.exec(count_q).one())


@router.get("/applications/{app_id}", response_model=ApplicationDetailOut)
def get_application(app_id: str, session: Session = Depends(get_session)) -> ApplicationDetailOut:
    app = get_app(session, app_id)
    return detail(session, app, office_names(session).get(app.office_id, app.office_id))


@router.patch("/applications/{app_id}", response_model=ApplicationSummaryOut)
def officer_action(app_id: str, body: OfficerActionIn, session: Session = Depends(get_session)) -> ApplicationSummaryOut:
    app = get_app(session, app_id)
    if app.status in DECIDED:
        raise api_error(409, "ALREADY_DECIDED", f"Application {app_id} is already {app.status}")
    if body.action in ("reject", "request_fix") and not body.reason_code:
        raise api_error(422, "REASON_REQUIRED", f"{body.action} needs a reason_code")

    # Contract v1.4: with a role, it must be the application's current stage, and only the Tahsildar decides.
    # Without a role the old single-officer behaviour is kept.
    if body.role is not None:
        if app.status != "ready_for_officer" or app.stage != body.role:
            raise api_error(409, "STAGE_MISMATCH",
                            f"Application is at stage {app.stage or 'none'}, not {body.role}")
        if body.action in ("approve", "reject") and body.role != "tahsildar":
            raise api_error(409, "STAGE_MISMATCH", f"Only the Tahsildar can {body.action}; forward it first")
    if body.action == "forward" and (app.status != "ready_for_officer" or next_stage(app.stage) is None):
        raise api_error(409, "CANNOT_FORWARD", "Only an application waiting with the VAO or RI can be forwarded")

    now = utc_now()
    docs = documents_of(session, app.id)
    if body.action == "forward":
        previous, app.stage = app.stage, next_stage(app.stage)
        app.stage_entered_at = now
        add_event(session, app.id, "forwarded", body.role or "officer",
                  f"{previous} → {app.stage}" + (f"; note: {body.note}" if body.note else ""))
        app.updated_at = now
        session.add(app)
        session.commit()
        session.refresh(app)
        return summary(app, office_names(session).get(app.office_id, app.office_id), docs)
    if body.action in ("approve", "reject"):
        app.status = "approved" if body.action == "approve" else "rejected"
        app.decision_action = body.action
        app.decision_reason = body.reason_code
        app.decision_note = body.note
        app.decided_at = now
        app.stage = None
        app.stage_entered_at = None
        # Privacy rule: card images are deleted as soon as the application is decided.
        for doc in docs:
            delete_image(doc.id)
            doc.image_path = None
            session.add(doc)
        reason = f" ({body.reason_code})" if body.reason_code else ""
        add_event(session, app.id, app.status, body.role or "officer",
                  f"{app.status}{reason}; {len(docs)} card images deleted" + (f"; note: {body.note}" if body.note else ""))
    else:
        app.status = "needs_fix"
        app.stage = None
        app.stage_entered_at = None
        add_event(session, app.id, "fix_requested", body.role or "officer",
                  body.reason_code + (f"; note: {body.note}" if body.note else ""))
    app.updated_at = now
    notify_decision(session, app, body.action, body.reason_code)
    session.add(app)
    session.commit()
    session.refresh(app)
    return summary(app, office_names(session).get(app.office_id, app.office_id), docs)
