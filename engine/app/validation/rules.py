"""Checksum / format rules behind the confidence gate.

"Can't read" is never "invalid": rules run only when quality passed and the ID-number OCR confidence
clears `ocr_min_confidence_for_rules`. A failing number is only called invalid when an independent
second read of the number region agrees with the first; otherwise the citizen is asked to retake.
"""
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from app.validation.messages import make_issue
from app.validation.types import Issue

PAN_RE = re.compile(r"^[A-Z]{5}[0-9]{4}[A-Z]$")
PAN_HOLDER = set("PCHFATBLJG")
EPIC_RE = re.compile(r"^[A-Z]{3}[0-9]{7}$")

_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]


def verhoeff_valid(digits: str) -> bool:
    if not digits or not digits.isdigit():
        return False
    c = 0
    for i, ch in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][int(ch)]]
    return c == 0


def check_number(doc_type: str, number: str) -> str | None:
    """None if valid, else the failing code (INVALID_FORMAT / INVALID_CHECKSUM)."""
    if doc_type in ("aadhaar_front", "aadhaar_back"):
        if len(number) != 12 or not number.isdigit() or number[0] in "01":
            return "INVALID_FORMAT"
        return None if verhoeff_valid(number) else "INVALID_CHECKSUM"
    if doc_type == "pan":
        return None if PAN_RE.match(number) and number[3] in PAN_HOLDER else "INVALID_FORMAT"
    if doc_type == "voter_id":
        return None if EPIC_RE.match(number) else "INVALID_FORMAT"
    return None


@dataclass
class RuleResult:
    issues: list[Issue] = field(default_factory=list)
    number: str | None = None  # final number (possibly corrected by the second read)
    trusted: bool = False  # number is readable and valid -> safe to HMAC / display


def apply_rules(doc_type: str, number: str | None, confidence: float | None, subs: int, min_conf: float,
                second_read: Callable[[], tuple[str | None, float | None]] | None = None) -> RuleResult:
    if not number:
        return RuleResult([make_issue("UNREADABLE", {"reason": "id_number_not_found"})])
    conf = confidence or 0.0
    if conf < min_conf:
        return RuleResult([make_issue("UNREADABLE", {"id_number_confidence": round(conf, 3),
                                                     "threshold": min_conf})], number)
    failure = check_number(doc_type, number)
    if doc_type in ("aadhaar_front", "aadhaar_back") and len(number) != 12:
        return RuleResult([make_issue("UNREADABLE", {"reason": "number_length", "digits_read": len(number)})], number)
    if failure is None:
        issues = [make_issue("OCR_AUTOCORRECTED", {"substitutions": subs})] if subs else []
        return RuleResult(issues, number, True)

    # Second, independent read of the number region before calling a genuine card invalid.
    if second_read is not None:
        n2, c2 = second_read()
        if n2 and n2 != number:
            if check_number(doc_type, n2) is None and (c2 or 0) >= min_conf:
                return RuleResult([make_issue("OCR_AUTOCORRECTED", {"second_read": True})], n2, True)
            return RuleResult([make_issue("UNREADABLE", {"reason": "reads_disagree",
                                                         "id_number_confidence": round(conf, 3),
                                                         "threshold": min_conf})], number)
        if not n2:
            return RuleResult([make_issue("UNREADABLE", {"reason": "second_read_failed",
                                                         "id_number_confidence": round(conf, 3),
                                                         "threshold": min_conf})], number)
    return RuleResult([make_issue(failure, {"id_number_confidence": round(conf, 3),
                                            "min_confidence_for_rules": min_conf,
                                            "confirmed_by_second_read": second_read is not None})], number)
