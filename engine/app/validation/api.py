"""Public engine interface used by routers and by Person 2's ops code (contract §4).

validate_image: file checks -> quality gate (early return) -> OCR -> classify -> extract -> rules.
"""
import logging
import time

import cv2
import imagehash
import numpy as np
from PIL import Image

from app.core.security import aadhaar_hmac, mask_aadhaar
from app.validation import ocr
from app.validation.classify import classify
from app.validation.consistency import check_consistency  # noqa: F401  (re-exported, contract §4)
from app.validation.duplicates import find_duplicates  # noqa: F401  (re-exported, contract §4)
from app.validation.extract import extract
from app.validation.messages import make_issue
from app.validation.quality import assess
from app.validation.rules import apply_rules
from app.validation.thresholds import get_thresholds
from app.validation.types import (DECLARABLE_TYPES, SUPPORTING_TYPES, ExtractedDoc, OcrInfo, Quality, Timings,
                                  ValidationOutcome, ValidationResult, doc_status)

log = logging.getLogger("sevaicheck.validate")

MAX_BYTES = 10 * 1024 * 1024
AADHAAR_TYPES = ("aadhaar_front", "aadhaar_back")


def sniff_image(data: bytes) -> str | None:
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def _file_rejection(code: str, declared_type: str | None, t0: float, evidence: dict) -> ValidationOutcome:
    issues = [make_issue(code, evidence)]
    result = ValidationResult(doc_type="unknown", declared_type=declared_type, status=doc_status(issues),
                              issues=issues, quality=Quality(card_found=False, passed=False),
                              timings_ms=Timings(quality=0, ocr=0, total=_ms(t0)))
    return ValidationOutcome(result=result)


def _jpeg(card: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", card, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return buf.tobytes()


def _phash(card: np.ndarray) -> str:
    return str(imagehash.phash(Image.fromarray(cv2.cvtColor(card, cv2.COLOR_BGR2RGB))))


def _scaled_read(card: np.ndarray, doc_type: str, scale: float):
    """Re-OCR the whole card at another scale and re-extract (a read independent of the first pass)."""
    big = cv2.resize(card, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    return extract(doc_type, [ocr.OcrToken(tk.text, tk.conf, tuple(v / scale for v in tk.bbox))
                              for tk in ocr.read(big)])


def _second_reader(card: np.ndarray, doc_type: str):
    """Second read used before declaring a number invalid: whole card at 1.3x."""
    def run() -> tuple[str | None, float | None]:
        ex = _scaled_read(card, doc_type, 1.3)
        return ex.id_number, ex.id_confidence
    return run


def _validate_supporting(image_bytes: bytes, declared_type: str, t0: float) -> ValidationOutcome:
    """Contract v1.4: page quality first (no OCR on a bad photo), then a keyword sanity check."""
    from app.validation.supporting import content_check, page_quality

    q, issues, page = page_quality(image_bytes)
    t_quality = _ms(t0)
    if page is None or any(i.severity == "blocking" for i in issues):
        result = ValidationResult(doc_type=declared_type, declared_type=declared_type, status=doc_status(issues),
                                  issues=issues, quality=Quality(**q),
                                  timings_ms=Timings(quality=t_quality, ocr=0, total=_ms(t0)))
        return ValidationOutcome(result=result, card_jpeg=_jpeg(page) if page is not None else None)
    t1 = time.perf_counter()
    more, fields, mean_conf = content_check(page, declared_type)
    issues += more
    detected = next((i.evidence["detected"] for i in more if i.code == "WRONG_DOC_TYPE"), declared_type)
    result = ValidationResult(doc_type=detected, declared_type=declared_type, status=doc_status(issues),
                              issues=issues, quality=Quality(**q), fields=fields,
                              ocr=OcrInfo(mean_confidence=round(mean_conf, 3), id_number_confidence=None),
                              timings_ms=Timings(quality=t_quality, ocr=_ms(t1), total=_ms(t0)))
    return ValidationOutcome(result=result, card_jpeg=_jpeg(page), phash=None, extracted=None)


def _try_eaadhaar_page(image_bytes: bytes, declared_type: str, t0: float, t: dict) -> ValidationOutcome | None:
    """Full e-Aadhaar letter path (see aadhaar_page.py). Returns None when the photo is not an e-Aadhaar letter."""
    from app.validation.aadhaar_page import best_number, read_page
    from app.validation.quality import decode
    from app.validation.supporting import page_quality

    q, q_issues, _page = page_quality(image_bytes)
    q_issues = [i for i in q_issues if i.code != "GLARE"]  # white paper, not a glossy card
    q["passed"] = not any(i.severity == "blocking" for i in q_issues)
    t_quality = _ms(t0)
    decoded = decode(image_bytes)
    if decoded is None:
        return None
    img, _ = decoded
    t1 = time.perf_counter()
    r = read_page(img)
    if not r.is_letter:
        return None
    issues = list(q_issues)
    if any(i.severity == "blocking" for i in issues):  # a letter, but too blurry/dark to read: retake
        result = ValidationResult(doc_type=declared_type, declared_type=declared_type, status=doc_status(issues),
                                  issues=issues, quality=Quality(**q),
                                  timings_ms=Timings(quality=t_quality, ocr=_ms(t1), total=_ms(t0)))
        return ValidationOutcome(result=result)
    number, conf, second = best_number(r)
    rr = apply_rules("aadhaar_front", number, conf, 0, t["ocr_min_confidence_for_rules"],
                     lambda: second if second else (None, None))
    issues.append(make_issue("EAADHAAR_PAGE", {"printings_of_number": len([n for n, _ in r.numbers if n == number]),
                                                "markers": r.markers}))
    issues.extend(rr.issues)
    display = mask_aadhaar(rr.number) if rr.number else None
    if declared_type == "aadhaar_back":
        fields = {"id_number_display": display, "pin_code": r.pin_code}
    else:
        fields = {"id_number_display": display, "name": r.name, "dob": r.dob, "gender": r.gender, "father_name": None}
    hmac_hex = aadhaar_hmac(rr.number) if rr.trusted and rr.number else None
    extracted = ExtractedDoc(doc_type=declared_type, declared_type=declared_type, name=r.name, dob=r.dob,
                             gender=r.gender, id_last4=rr.number[-4:] if rr.number else None)
    result = ValidationResult(doc_type=declared_type, declared_type=declared_type, status=doc_status(issues),
                              issues=issues, quality=Quality(**q), fields=fields,
                              ocr=OcrInfo(mean_confidence=round(r.mean_conf, 3),
                                          id_number_confidence=None if conf is None else round(conf, 3)),
                              timings_ms=Timings(quality=t_quality, ocr=_ms(t1), total=_ms(t0)))
    jpeg = _jpeg(cv2.resize(img, None, fx=min(1.0, 1600 / max(img.shape[:2])), fy=min(1.0, 1600 / max(img.shape[:2]))))
    log.info("validate e-aadhaar page status=%s codes=%s ms=%s", result.status, [i.code for i in issues],
             result.timings_ms.total)
    return ValidationOutcome(result=result, aadhaar_hmac=hmac_hex, phash=None, card_jpeg=jpeg, extracted=extracted)


def _ocr_and_classify(card: np.ndarray, declared_type: str | None, min_score: float):
    tokens = ocr.read(card)
    detected, scores = classify(tokens, declared_type, min_score)
    if detected == "unknown":  # maybe upside down: try once rotated 180 degrees
        flipped = cv2.rotate(card, cv2.ROTATE_180)
        tokens2 = ocr.read(flipped)
        detected2, scores2 = classify(tokens2, declared_type, min_score)
        if detected2 != "unknown":
            return flipped, tokens2, detected2, scores2
    return card, tokens, detected, scores


def validate_image(image_bytes: bytes, declared_type: str | None = None) -> ValidationOutcome:
    t0 = time.perf_counter()
    if declared_type not in DECLARABLE_TYPES:
        declared_type = None
    if len(image_bytes) > MAX_BYTES:
        return _file_rejection("FILE_TOO_LARGE", declared_type, t0,
                               {"size_mb": round(len(image_bytes) / 1048576, 2), "max_mb": 10})
    if sniff_image(image_bytes) is None:
        return _file_rejection("UNSUPPORTED_FILE", declared_type, t0, {"detected": "not jpg/png"})

    if declared_type in SUPPORTING_TYPES:
        return _validate_supporting(image_bytes, declared_type, t0)

    t = get_thresholds()
    rep = assess(image_bytes)
    out = _validate_card(image_bytes, declared_type, t0, t, rep)
    codes = {i.code for i in out.result.issues if i.severity == "blocking"}
    if declared_type in AADHAAR_TYPES and codes and codes <= PAGE_RETRY_CODES:
        page = _try_eaadhaar_page(image_bytes, declared_type, t0, t)
        if page is not None:  # a full e-Aadhaar letter, not a bad card photo
            return page
    return out


# Card-path failures that may simply mean "this is a whole e-Aadhaar letter, not a card".
PAGE_RETRY_CODES = {"CARD_NOT_FOUND", "CROPPED", "TOO_BRIGHT", "WRONG_DOC_TYPE", "UNKNOWN_DOC_TYPE", "UNREADABLE"}


def _validate_card(image_bytes: bytes, declared_type: str | None, t0: float, t: dict, rep) -> ValidationOutcome:
    t_quality = _ms(t0)
    quality = Quality(**rep.quality)
    issues = list(rep.issues)
    if rep.card is None or rep.blocking:
        # Quality first: never run OCR on a bad capture.
        result = ValidationResult(doc_type="unknown", declared_type=declared_type, status=doc_status(issues),
                                  issues=issues, quality=quality,
                                  timings_ms=Timings(quality=t_quality, ocr=0, total=_ms(t0)))
        return ValidationOutcome(result=result)

    t1 = time.perf_counter()
    card, tokens, detected, scores = _ocr_and_classify(rep.card, declared_type, t["classify_min_score"])
    mean_conf = float(np.mean([tk.conf for tk in tokens])) if tokens else 0.0
    card_jpeg, phash = _jpeg(card), _phash(card)

    def finish(doc_type: str, fields: dict | None, id_conf: float | None, extracted: ExtractedDoc | None = None,
               hmac_hex: str | None = None) -> ValidationOutcome:
        result = ValidationResult(
            doc_type=doc_type, declared_type=declared_type, status=doc_status(issues), issues=issues,
            quality=quality, fields=fields,
            ocr=OcrInfo(mean_confidence=round(mean_conf, 3),
                        id_number_confidence=None if id_conf is None else round(id_conf, 3)),
            timings_ms=Timings(quality=t_quality, ocr=_ms(t1), total=_ms(t0)))
        return ValidationOutcome(result=result, aadhaar_hmac=hmac_hex, phash=phash, card_jpeg=card_jpeg,
                                 extracted=extracted)

    if detected == "unknown":
        issues.append(make_issue("UNKNOWN_DOC_TYPE", {"best_score": max(scores.values()),
                                                      "threshold": t["classify_min_score"]}))
        return finish("unknown", None, None)
    if declared_type and detected != declared_type:
        issues.append(make_issue("WRONG_DOC_TYPE", {"declared": declared_type, "detected": detected,
                                                    "score": scores[detected]}))
        return finish(detected, None, None)

    ex = extract(detected, tokens)
    if not ex.id_number or (ex.id_confidence or 0) < t["ocr_min_confidence_for_rules"]:
        # One retry at 1.5x before asking for a retake (small text / clipped first character).
        ex2 = _scaled_read(card, detected, 1.5)
        if ex2.id_number and (ex2.id_confidence or 0) > (ex.id_confidence or 0):
            ex2.name, ex2.dob = ex2.name or ex.name, ex2.dob or ex.dob
            ex2.gender, ex2.father_name = ex2.gender or ex.gender, ex2.father_name or ex.father_name
            ex2.pin_code = ex2.pin_code or ex.pin_code
            ex = ex2
    rr = apply_rules(detected, ex.id_number, ex.id_confidence, ex.id_subs, t["ocr_min_confidence_for_rules"],
                     _second_reader(card, detected))
    issues.extend(rr.issues)
    number = rr.number

    if detected in AADHAAR_TYPES:
        display = mask_aadhaar(number) if number else None
    else:
        display = number
    if detected == "aadhaar_back":
        fields = {"id_number_display": display, "pin_code": ex.pin_code}
    else:
        fields = {"id_number_display": display, "name": ex.name, "dob": ex.dob, "gender": ex.gender,
                  "father_name": ex.father_name}

    hmac_hex = None
    if detected in AADHAAR_TYPES and rr.trusted and number and len(number) == 12:
        hmac_hex = aadhaar_hmac(number)
    extracted = ExtractedDoc(doc_type=detected, declared_type=declared_type, name=ex.name, dob=ex.dob,
                             gender=ex.gender, father_name=ex.father_name,
                             id_last4=number[-4:] if number and len(number) >= 4 else None)
    out = finish(detected, fields, ex.id_confidence, extracted, hmac_hex)
    log.info("validate doc=%s status=%s codes=%s ms=%s", detected, out.result.status,
             [i.code for i in issues], out.result.timings_ms.total)  # never log numbers or names
    return out
