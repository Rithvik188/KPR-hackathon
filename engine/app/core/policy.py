"""Central permission table, enforced on the server for every /api route (deny by default).

Every request is matched against POLICY by method + path. The rule says which roles may call it and, for single
records, an ownership check against the database:
- officers (VAO / RI / Tahsildar) may read any application and act only at their own stage;
- e-Sevai operators may only touch applications of their own centre;
- citizens may only touch applications and the CAN profile that belong to their own phone number.
The browser's role/stage claims are never trusted: the role comes from the signed token.
"""
import json
import re
from collections.abc import Callable

from fastapi import Request
from sqlmodel import Session

from app.core.auth import STAFF_ROLES, Principal, rate_limited, verify_token
from app.core.config import get_settings
from app.core.db import engine
from app.core.errors import api_error
from app.core.models import Application, Citizen, Document

PUBLIC = "public"
ANY = ("citizen", "operator") + STAFF_ROLES
OFFICERS = STAFF_ROLES
FRONTLINE = ("citizen", "operator")


def _app_of(session: Session, app_id: str) -> Application:
    app = session.get(Application, app_id)
    if app is None:
        raise api_error(404, "APPLICATION_NOT_FOUND", f"No application {app_id}")
    return app


def _owns(session: Session, p: Principal, app: Application) -> bool:
    if p.is_staff:
        return True
    if p.role == "operator":
        return app.office_id == p.office_id
    if app.can_id:  # citizen: the application's CAN must belong to the signed-in phone
        c = session.get(Citizen, app.can_id)
        return c is not None and c.phone_hmac == p.sub
    return False


async def check_app(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    if not _owns(session, p, _app_of(session, m["app"])):
        raise api_error(403, "FORBIDDEN", "This application belongs to someone else")


async def check_image(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    doc = session.get(Document, m["doc"])
    if doc is None or not _owns(session, p, _app_of(session, doc.application_id)):
        raise api_error(404, "NOT_FOUND", "No such image")  # don't reveal that it exists


async def check_officer_action(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    app = _app_of(session, m["app"])
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        body = {}
    action = body.get("action")
    if body.get("role") not in (None, p.role):
        raise api_error(403, "FORBIDDEN", "The role in the request does not match your sign-in")
    if action in ("approve", "reject") and p.role != "tahsildar":
        raise api_error(403, "FORBIDDEN", "Only the Tahsildar can approve or reject")
    if action in ("forward", "approve", "reject") and app.stage and app.stage != p.role:
        raise api_error(409, "STAGE_MISMATCH", f"This application is with the {app.stage.upper()}, not you")


async def check_create_application(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    try:
        body = json.loads(await request.body() or b"{}")
    except json.JSONDecodeError:
        return
    if p.role == "operator" and body.get("office_id") not in (None, p.office_id):
        raise api_error(403, "FORBIDDEN", "Operators can only create applications at their own centre")
    if p.role == "citizen":
        can = body.get("can")
        c = session.get(Citizen, str(can).strip().upper()) if can else None
        if c is None or c.phone_hmac != p.sub:
            raise api_error(403, "FORBIDDEN", "Citizens apply with their own CAN (sign in with its mobile number)")


async def check_citizen_create(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    if p.role != "citizen":
        return
    from app.core.security import phone_hmac
    try:
        body = json.loads(await request.body() or b"{}")
        if phone_hmac(body.get("phone", "")) != p.sub:
            raise ValueError
    except Exception:  # noqa: BLE001
        raise api_error(403, "FORBIDDEN", "Citizens can only create a CAN for their own mobile number") from None


async def check_citizen_read(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    if p.role == "citizen":
        c = session.get(Citizen, m["can"].strip().upper())
        if c is None or c.phone_hmac != p.sub:
            raise api_error(404, "CAN_NOT_FOUND", "No such CAN")


async def check_alerts(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    if p.role == "operator" and request.query_params.get("office_id") != p.office_id:
        raise api_error(403, "FORBIDDEN", "Operators see only their own centre's notices (?office_id=)")


async def check_notifications(request: Request, p: Principal, session: Session, m: re.Match) -> None:
    if p.is_staff:
        return
    app_id = request.query_params.get("application_id")
    if not app_id or not _owns(session, p, _app_of(session, app_id)):
        raise api_error(403, "FORBIDDEN", "Ask for the notifications of your own application (?application_id=)")


Check = Callable | None
# (method, path regex, allowed roles or PUBLIC, extra check)
POLICY: list[tuple[str, str, object, Check]] = [
    ("GET", r"/health", PUBLIC, None),
    ("GET", r"/offices", PUBLIC, None),
    ("GET", r"/metrics/detection", PUBLIC, None),
    ("POST", r"/auth/(staff|otp/request|otp/verify)", PUBLIC, None),
    ("GET", r"/auth/me", ANY, None),
    ("POST", r"/issues", PUBLIC, None),  # anyone may report a problem at a centre (rate limited)
    ("GET", r"/issues", OFFICERS, None),
    ("POST", r"/validate", ANY, None),
    ("GET", r"/metrics/operations", OFFICERS + ("operator",), None),
    ("GET", r"/alerts", OFFICERS + ("operator",), check_alerts),
    ("POST", r"/alerts/(?P<id>[^/]+)/ack", OFFICERS, None),
    ("GET", r"/notifications", ANY, check_notifications),
    ("POST", r"/citizens", FRONTLINE, check_citizen_create),
    ("GET", r"/citizens/(?P<can>[^/]+)", FRONTLINE + OFFICERS, check_citizen_read),
    ("POST", r"/applications", FRONTLINE, check_create_application),
    ("GET", r"/applications", OFFICERS, None),
    ("GET", r"/applications/(?P<app>[^/]+)", ANY, check_app),
    ("PATCH", r"/applications/(?P<app>[^/]+)", OFFICERS, check_officer_action),
    ("POST", r"/applications/(?P<app>[^/]+)/documents", FRONTLINE, check_app),
    ("GET", r"/documents/(?P<doc>[^/]+)/image", ANY, check_image),
]
_COMPILED = [(m, re.compile(rf"^/api{p}$"), roles, chk) for m, p, roles, chk in POLICY]


def principal_of(request: Request) -> Principal | None:
    auth = request.headers.get("authorization", "")
    return verify_token(auth[7:].strip()) if auth.lower().startswith("bearer ") else None


async def authorize(request: Request) -> None:
    """FastAPI dependency on every /api route: identify, rate-limit, then allow or deny by POLICY."""
    p = principal_of(request)
    request.state.principal = p
    ip = request.client.host if request.client else "?"
    # Anonymous and citizen traffic is held tight; signed-in staff (officer screens, audits) get a higher ceiling.
    staff = p is not None and p.is_staff
    if rate_limited(f"api:{p.sub if staff else ip}", 20000 if staff else 600, 60):
        raise api_error(429, "TOO_MANY_REQUESTS", "Too many requests. Slow down.")
    if request.method == "POST" and not staff and rate_limited(f"post:{ip}", 60, 60):
        raise api_error(429, "TOO_MANY_REQUESTS", "Too many uploads or submissions. Slow down.")
    if not get_settings().auth_required:
        return  # explicit opt-out (local development only); docs/SECURITY.md
    path = request.url.path
    for method, rx, roles, chk in _COMPILED:
        mm = rx.match(path)
        if method == request.method and mm:
            if roles == PUBLIC:
                return
            if p is None:
                raise api_error(401, "NOT_SIGNED_IN", "Sign in first")
            if p.role not in roles:
                raise api_error(403, "FORBIDDEN", "Your role cannot do this")
            if chk:
                with Session(engine) as session:
                    await chk(request, p, session, mm)
            return
    raise api_error(403, "FORBIDDEN", "Not allowed")  # deny by default: every route must be in POLICY
