"""Issue construction. Severity/audience mirror contract §1; text comes from contract/messages.json."""
import json
from functools import lru_cache
from typing import Any

from app.core.config import CONTRACT_DIR
from app.validation.types import Issue

# code -> (severity, audience)
CODE_TABLE: dict[str, tuple[str, str]] = {
    "FILE_TOO_LARGE": ("blocking", "citizen"),
    "UNSUPPORTED_FILE": ("blocking", "citizen"),
    "CARD_NOT_FOUND": ("blocking", "citizen"),
    "CROPPED": ("blocking", "citizen"),
    "BLUR": ("blocking", "citizen"),
    "GLARE": ("blocking", "citizen"),
    "TOO_DARK": ("blocking", "citizen"),
    "TOO_BRIGHT": ("blocking", "citizen"),
    "LOW_RESOLUTION": ("blocking", "citizen"),
    "SKEW_CORRECTED": ("info", "officer"),
    "UNKNOWN_DOC_TYPE": ("blocking", "citizen"),
    "WRONG_DOC_TYPE": ("blocking", "citizen"),
    "UNREADABLE": ("blocking", "citizen"),
    "INVALID_CHECKSUM": ("blocking", "citizen"),
    "INVALID_FORMAT": ("blocking", "citizen"),
    "OCR_AUTOCORRECTED": ("info", "officer"),
    "DUPLICATE_SUSPECTED": ("warning", "officer"),
    "AADHAAR_BACK_MISSING": ("blocking", "citizen"),
    "NAME_LIKELY_MATCH": ("warning", "officer"),
    "NAME_MISMATCH": ("blocking", "citizen"),
    "DOB_MISMATCH": ("blocking", "citizen"),
}

QUALITY_CODES = ("CARD_NOT_FOUND", "CROPPED", "BLUR", "GLARE", "TOO_DARK", "TOO_BRIGHT", "LOW_RESOLUTION")


@lru_cache
def _messages() -> dict[str, dict[str, str]]:
    data = json.loads((CONTRACT_DIR / "messages.json").read_text(encoding="utf-8"))
    missing = [c for c in CODE_TABLE if c not in data]
    if missing:
        raise RuntimeError(f"contract/messages.json is missing codes: {missing}")
    return data


def _clean(value: Any) -> Any:
    if isinstance(value, float):
        return round(value, 4)
    if hasattr(value, "item"):  # numpy scalar
        return _clean(value.item())
    return value


def make_issue(code: str, evidence: dict[str, Any] | None = None) -> Issue:
    severity, audience = CODE_TABLE[code]
    msg = _messages()[code]
    ev = {k: _clean(v) for k, v in (evidence or {}).items()}
    return Issue(code=code, severity=severity, audience=audience, msg_en=msg["en"], msg_ta=msg["ta"], evidence=ev)
