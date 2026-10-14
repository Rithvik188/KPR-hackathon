"""Database tables (contract §5). Datetimes are timezone-aware UTC (sqlmodel requires tz); use `iso()` for API output."""
import secrets
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def utcnow() -> datetime:
    return datetime.now(UTC)


def iso(dt: datetime | None) -> str | None:
    """ISO 8601 UTC with a trailing Z, as the contract requires."""
    if dt is None:
        return None
    dt = dt.astimezone(UTC).replace(tzinfo=None) if dt.tzinfo else dt  # naive values are treated as UTC
    return dt.replace(microsecond=0).isoformat() + "Z"


def new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


class Office(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    type: str  # taluk_office | esevai_centre
    taluk: str
    lat: float
    lng: float


class Application(SQLModel, table=True):
    id: str = Field(primary_key=True)
    citizen_name: str
    citizen_dob: str | None = None  # ISO date typed by the operator (contract v1.4)
    phone_masked: str
    service: str
    office_id: str = Field(index=True, foreign_key="office.id")
    status: str = Field(index=True)
    created_at: datetime = Field(default_factory=utcnow, index=True)
    updated_at: datetime = Field(default_factory=utcnow)
    sla_due_at: datetime
    resubmissions: int = 0
    decision_action: str | None = None
    decision_reason: str | None = None
    decision_note: str | None = None
    decided_at: datetime | None = None
    stage: str | None = Field(default=None, index=True)  # vao | ri | tahsildar (contract v1.4)
    stage_entered_at: datetime | None = None
    consistency_json: str | None = None  # latest ConsistencyResult, cached by ops (contract v1.2)
    is_seed: bool = Field(default=False, index=True)


class Document(SQLModel, table=True):
    id: str = Field(primary_key=True)
    application_id: str = Field(index=True, foreign_key="application.id")
    doc_type: str  # detected type ("unknown" on a quality early-return)
    declared_type: str | None = None  # slot the operator uploaded into (contract v1.1)
    status: str
    issues_json: str = "[]"
    fields_json: str | None = None
    extracted_json: str | None = None  # ExtractedDoc, never the full ID number
    aadhaar_hmac: str | None = Field(default=None, index=True)
    phash: str | None = None
    image_path: str | None = None
    uploaded_at: datetime = Field(default_factory=utcnow, index=True)
    is_seed: bool = Field(default=False, index=True)


class AppEvent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    application_id: str = Field(index=True, foreign_key="application.id")
    at: datetime = Field(default_factory=utcnow)
    event: str
    actor: str
    note: str | None = None


class Alert(SQLModel, table=True):
    id: str = Field(primary_key=True)
    rule: str
    severity: str
    office_id: str | None = Field(default=None, index=True)
    title_en: str
    detail_en: str
    evidence_json: str = "{}"
    suggested_action_en: str
    status: str = "open"
    created_at: datetime = Field(default_factory=utcnow)
    dedupe_key: str = Field(index=True, unique=True)


class IssueReport(SQLModel, table=True):
    id: str = Field(primary_key=True)
    office_id: str = Field(index=True)
    category: str
    description: str
    reporter_role: str
    created_at: datetime = Field(default_factory=utcnow, index=True)


class Notification(SQLModel, table=True):
    id: str = Field(primary_key=True)
    application_id: str = Field(index=True)
    channel: str = "sms"
    to_masked: str
    body_en: str
    body_ta: str
    created_at: datetime = Field(default_factory=utcnow)
