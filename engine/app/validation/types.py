"""Contract shapes (api.md §2) plus the internal outcome passed to ops (api.md §4)."""
from dataclasses import asdict, dataclass
from typing import Any, Literal

from pydantic import BaseModel, Field

DocType = Literal["aadhaar_front", "aadhaar_back", "pan", "voter_id", "unknown", "parent_community_certificate",
                  "birth_certificate", "income_proof", "address_proof"]
DocStatus = Literal["accepted", "fixable", "invalid"]
Severity = Literal["blocking", "warning", "info"]
Audience = Literal["citizen", "officer"]
NameTier = Literal["match", "likely_match", "mismatch", "not_enough_data"]

ID_TYPES = ("aadhaar_front", "aadhaar_back", "pan", "voter_id")
SUPPORTING_TYPES = ("parent_community_certificate", "birth_certificate", "income_proof", "address_proof")
DECLARABLE_TYPES = ID_TYPES + SUPPORTING_TYPES


class Issue(BaseModel):
    code: str
    severity: Severity
    audience: Audience
    msg_en: str
    msg_ta: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class Quality(BaseModel):
    card_found: bool
    blur_score: float | None = None
    glare_fraction: float | None = None
    brightness: float | None = None
    skew_deg: float | None = None
    card_width_px: int | None = None
    passed: bool


class OcrInfo(BaseModel):
    mean_confidence: float
    id_number_confidence: float | None = None


class Timings(BaseModel):
    quality: int
    ocr: int
    total: int


class ValidationResult(BaseModel):
    document_id: str | None = None
    doc_type: DocType
    declared_type: str | None = None
    status: DocStatus
    issues: list[Issue]
    quality: Quality
    # Per-type keys: id_number_display, name, dob, gender, father_name (aadhaar_back: id_number_display, pin_code)
    fields: dict[str, Any] | None = None
    ocr: OcrInfo | None = None
    timings_ms: Timings


class ConsistencyResult(BaseModel):
    name_tier: NameTier
    name_score: float | None = None
    names_compared: list[str] = Field(default_factory=list)
    dob_match: bool | None = None
    issues: list[Issue] = Field(default_factory=list)
    # v1.4: operator-typed form vs documents; None unless check_consistency(..., form=...) was used
    form_check: dict[str, Any] | None = None


@dataclass
class ExtractedDoc:
    """Fields needed for cross-document checks. Never holds the full ID number."""
    doc_type: str
    declared_type: str | None = None
    name: str | None = None
    dob: str | None = None  # ISO yyyy-mm-dd
    gender: str | None = None
    father_name: str | None = None
    id_last4: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ExtractedDoc":
        return cls(**{k: d.get(k) for k in cls.__dataclass_fields__})


@dataclass
class ValidationOutcome:
    result: ValidationResult
    aadhaar_hmac: str | None = None
    phash: str | None = None
    card_jpeg: bytes | None = None
    extracted: ExtractedDoc | None = None


def doc_status(issues: list[Issue]) -> DocStatus:
    """Contract §1 DocStatus rule."""
    if any(i.code.startswith("INVALID_") for i in issues):
        return "invalid"
    if any(i.severity == "blocking" for i in issues):
        return "fixable"
    return "accepted"
