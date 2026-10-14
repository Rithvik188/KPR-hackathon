"""Public engine interface used by routers and by Person 2's ops code (contract §4).

STUB (Sync 1): contract-shaped fake results. Signatures are final.
"""
import io
import time

from PIL import Image

from app.validation.messages import make_issue
from app.validation.types import (DECLARABLE_TYPES, ConsistencyResult, ExtractedDoc, Quality, Timings,
                                  ValidationOutcome, ValidationResult, doc_status)

MAX_BYTES = 10 * 1024 * 1024


def sniff_image(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None


def _file_rejection(code: str, declared_type: str | None, started: float, evidence: dict) -> ValidationOutcome:
    issues = [make_issue(code, evidence)]
    ms = int((time.perf_counter() - started) * 1000)
    result = ValidationResult(doc_type="unknown", declared_type=declared_type, status=doc_status(issues),
                              issues=issues, quality=Quality(card_found=False, passed=False),
                              timings_ms=Timings(quality=0, ocr=0, total=ms))
    return ValidationOutcome(result=result)


def validate_image(image_bytes: bytes, declared_type: str | None = None) -> ValidationOutcome:
    started = time.perf_counter()
    if declared_type not in DECLARABLE_TYPES:
        declared_type = None
    if len(image_bytes) > MAX_BYTES:
        return _file_rejection("FILE_TOO_LARGE", declared_type, started,
                               {"size_mb": round(len(image_bytes) / 1048576, 2), "max_mb": 10})
    if sniff_image(image_bytes) is None:
        return _file_rejection("UNSUPPORTED_FILE", declared_type, started, {"detected": "not jpg/png"})
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception:  # noqa: BLE001
        return _file_rejection("UNSUPPORTED_FILE", declared_type, started, {"detected": "undecodable"})
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)

    doc_type = declared_type or "aadhaar_front"
    issues = [make_issue("SKEW_CORRECTED", {"skew_deg": 7.4, "threshold": 2.0})]
    if doc_type == "aadhaar_back":
        fields = {"id_number_display": "XXXX XXXX 4321", "pin_code": "641402"}
    elif doc_type == "pan":
        fields = {"id_number_display": "ABCPK1234F", "name": "KARTHIK RAJENDRAN", "dob": "1998-04-12",
                  "gender": None, "father_name": "RAJENDRAN"}
    elif doc_type == "voter_id":
        fields = {"id_number_display": "ABC1234567", "name": "KARTHIK RAJENDRAN", "dob": "1998-04-12",
                  "gender": "M", "father_name": "RAJENDRAN"}
    else:
        fields = {"id_number_display": "XXXX XXXX 4321", "name": "R. KARTHIK", "dob": "1998-04-12",
                  "gender": "M", "father_name": None}
    ms = int((time.perf_counter() - started) * 1000)
    result = ValidationResult(
        doc_type=doc_type, declared_type=declared_type, status=doc_status(issues), issues=issues,
        quality=Quality(card_found=True, blur_score=312.5, glare_fraction=0.001, brightness=142.0, skew_deg=7.4,
                        card_width_px=img.width, passed=True),
        fields=fields, ocr={"mean_confidence": 0.91, "id_number_confidence": 0.94},
        timings_ms=Timings(quality=ms, ocr=0, total=ms))
    extracted = ExtractedDoc(doc_type=doc_type, declared_type=declared_type, name=fields.get("name"),
                             dob=fields.get("dob"), gender=fields.get("gender"),
                             father_name=fields.get("father_name"), id_last4="4321")
    return ValidationOutcome(result=result, aadhaar_hmac=None, phash=None, card_jpeg=buf.getvalue(),
                             extracted=extracted)


def check_consistency(docs: list[ExtractedDoc]) -> ConsistencyResult:
    return ConsistencyResult(name_tier="not_enough_data")


def find_duplicates(session, aadhaar_hmac: str | None, phash: str | None,
                    exclude_application_id: str) -> list[str]:
    return []
