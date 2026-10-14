"""User-reported issues: POST /issues (re-runs the USER_REPORTED rule at once) and GET /issues."""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.errors import api_error
from app.core.models import IssueReport, Office, iso, new_id
from app.ops import alerts
from app.ops.clock import now
from app.ops.schemas import IssueReportIn, IssueReportOut

router = APIRouter(tags=["ops"])


def to_out(r: IssueReport) -> IssueReportOut:
    return IssueReportOut(id=r.id, office_id=r.office_id, category=r.category,  # type: ignore[arg-type]
                          description=r.description, reporter_role=r.reporter_role,  # type: ignore[arg-type]
                          created_at=iso(r.created_at))


@router.post("/issues", status_code=201, response_model=IssueReportOut)
def create_issue(body: IssueReportIn, session: Session = Depends(get_session)) -> IssueReportOut:
    if session.get(Office, body.office_id) is None:
        raise api_error(400, "UNKNOWN_OFFICE", f"No office {body.office_id}")
    report = IssueReport(id=new_id("is"), office_id=body.office_id, category=body.category,
                         description=body.description.strip(), reporter_role=body.reporter_role, created_at=now())
    session.add(report)
    session.commit()
    session.refresh(report)
    alerts.evaluate_user_reported(session)
    return to_out(report)


@router.get("/issues", response_model=list[IssueReportOut])
def list_issues(office_id: str | None = None, limit: int = Query(50, ge=1, le=500),
                session: Session = Depends(get_session)) -> list[IssueReportOut]:
    q = select(IssueReport)
    if office_id:
        q = q.where(IssueReport.office_id == office_id)
    q = q.order_by(IssueReport.created_at.desc(), IssueReport.id).limit(limit)
    return [to_out(r) for r in session.exec(q).all()]
