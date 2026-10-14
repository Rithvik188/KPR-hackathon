"""Mock SMS notifications (bilingual) and GET /notifications.

Issue wording always comes from contract/messages.json (via make_issue); only the short SMS frame is here.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.core.db import get_session
from app.core.models import Application, Notification, iso, new_id
from app.ops.clock import now
from app.ops.schemas import NotificationOut
from app.validation.messages import CODE_TABLE, make_issue
from app.validation.types import Issue

router = APIRouter(tags=["ops"])

MAX_ISSUES_IN_SMS = 2


def _send(session: Session, app: Application, body_en: str, body_ta: str) -> Notification:
    n = Notification(id=new_id("nt"), application_id=app.id, channel="sms", to_masked=app.phone_masked,
                     body_en=body_en, body_ta=body_ta, created_at=now())
    session.add(n)
    return n


def _reason_text(reason_code: str | None) -> tuple[str, str]:
    """An issue code becomes its bilingual message; anything else is shown as-is."""
    if reason_code in CODE_TABLE:
        issue = make_issue(reason_code)
        return issue.msg_en, issue.msg_ta
    text = (reason_code or "").replace("_", " ").lower()
    return text, text


def notify_needs_fix(session: Session, app: Application, issues: list[Issue]) -> Notification:
    citizen = [i for i in issues if i.severity == "blocking" and i.audience == "citizen"][:MAX_ISSUES_IN_SMS]
    en = " ".join(i.msg_en for i in citizen)
    ta = " ".join(i.msg_ta for i in citizen)
    return _send(session, app,
                 f"SevaiCheck: Application {app.id} needs a correction. {en} Please visit the centre.",
                 f"SevaiCheck: விண்ணப்பம் {app.id}-க்கு திருத்தம் தேவை. {ta} மையத்திற்கு வரவும்.")


def notify_ready(session: Session, app: Application) -> Notification:
    return _send(session, app,
                 f"SevaiCheck: All documents for application {app.id} are verified and sent to the officer.",
                 f"SevaiCheck: விண்ணப்பம் {app.id}-இன் அனைத்து ஆவணங்களும் சரிபார்க்கப்பட்டு அலுவலருக்கு அனுப்பப்பட்டன.")


def notify_decision(session: Session, app: Application, action: str, reason_code: str | None) -> Notification:
    if action == "approve":
        return _send(session, app,
                     f"SevaiCheck: Your application {app.id} has been approved.",
                     f"SevaiCheck: உங்கள் விண்ணப்பம் {app.id} ஒப்புதல் பெற்றது.")
    reason_en, reason_ta = _reason_text(reason_code)
    if action == "reject":
        return _send(session, app,
                     f"SevaiCheck: Your application {app.id} was not approved. Reason: {reason_en}",
                     f"SevaiCheck: உங்கள் விண்ணப்பம் {app.id} ஏற்கப்படவில்லை. காரணம்: {reason_ta}")
    return _send(session, app,
                 f"SevaiCheck: The officer needs a correction for application {app.id}. {reason_en} "
                 f"Please visit the centre.",
                 f"SevaiCheck: விண்ணப்பம் {app.id}-க்கு அலுவலர் திருத்தம் கோருகிறார். {reason_ta} மையத்திற்கு வரவும்.")


def to_out(n: Notification) -> NotificationOut:
    return NotificationOut(id=n.id, application_id=n.application_id, channel=n.channel, to_masked=n.to_masked,
                           body_en=n.body_en, body_ta=n.body_ta, created_at=iso(n.created_at))


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(application_id: str | None = None, limit: int = 100,
                       session: Session = Depends(get_session)) -> list[NotificationOut]:
    q = select(Notification)
    if application_id:
        q = q.where(Notification.application_id == application_id)
    q = q.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(max(1, min(limit, 500)))
    return [to_out(n) for n in session.exec(q).all()]
