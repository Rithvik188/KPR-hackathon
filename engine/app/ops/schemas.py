"""Request and response models for the ops endpoints (contract §2), so /openapi.json and web's generated types
are exact. Engine shapes (Issue, ValidationResult, ConsistencyResult) are reused from Person 1's types.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.validation.types import ConsistencyResult, DocStatus, DocType, Issue, ValidationResult

Service = Literal["community_certificate", "income_certificate", "nativity_certificate", "ration_card_update"]
AppStatus = Literal["submitted", "needs_fix", "ready_for_officer", "approved", "rejected"]
OfficerAction = Literal["approve", "reject", "request_fix"]
OfficeType = Literal["taluk_office", "esevai_centre"]
IssueCategory = Literal["scanner_problem", "long_wait", "wrong_rejection", "other"]
ReporterRole = Literal["citizen", "operator", "officer"]


class OfficeOut(BaseModel):
    id: str
    name: str
    type: OfficeType
    taluk: str
    lat: float
    lng: float


class CreateApplicationIn(BaseModel):
    citizen_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=10, max_length=16)
    service: Service
    office_id: str


class OfficerActionIn(BaseModel):
    action: OfficerAction
    reason_code: str | None = None
    note: str | None = Field(default=None, max_length=500)


class ApplicationSummaryOut(BaseModel):
    id: str
    citizen_name: str
    phone_masked: str
    service: Service
    office_id: str
    office_name: str
    status: AppStatus
    created_at: str
    updated_at: str
    sla_due_at: str
    sla_hours_left: float
    flag_codes: list[str]
    doc_count: int
    resubmissions: int


class DocumentOut(BaseModel):
    id: str
    doc_type: DocType
    status: DocStatus
    issues: list[Issue]
    fields: dict[str, Any] | None
    uploaded_at: str
    image_available: bool


class HistoryEventOut(BaseModel):
    at: str
    event: str
    actor: str
    note: str | None


class DecisionOut(BaseModel):
    action: OfficerAction
    reason_code: str | None
    note: str | None
    at: str


class ApplicationDetailOut(ApplicationSummaryOut):
    documents: list[DocumentOut]
    consistency: ConsistencyResult
    history: list[HistoryEventOut]
    decision: DecisionOut | None


class ApplicationListOut(BaseModel):
    items: list[ApplicationSummaryOut]
    total: int


class UploadResultOut(BaseModel):
    document_id: str
    validation: ValidationResult
    application: ApplicationSummaryOut
    consistency: ConsistencyResult


class NotificationOut(BaseModel):
    id: str
    application_id: str
    channel: Literal["sms"]
    to_masked: str
    body_en: str
    body_ta: str
    created_at: str
