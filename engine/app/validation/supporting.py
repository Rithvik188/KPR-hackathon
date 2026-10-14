"""Supporting documents (contract v1.4): page-quality checks plus a keyword sanity check.

These are A4 papers (birth certificate, parent's community certificate, salary certificate, electricity bill), not
ID-1 cards, so there is no card detection. Their contents vary by issuer, so the officer verifies them; the engine
only makes sure the photo is readable and is not obviously the wrong document.
"""
import cv2
import numpy as np
from rapidfuzz import fuzz

from app.validation import ocr
from app.validation.classify import scores as id_scores
from app.validation.messages import make_issue
from app.validation.quality import decode, glare_fraction
from app.validation.text import squash
from app.validation.thresholds import get_thresholds
from app.validation.types import Issue

KEYWORDS = {
    "parent_community_certificate": ["COMMUNITYCERTIFICATE", "COMMUNITY", "CASTE"],
    "birth_certificate": ["BIRTHCERTIFICATE", "CERTIFICATEOFBIRTH", "PLACEOFBIRTH", "REGISTRATIONNO"],
    "income_proof": ["SALARYCERTIFICATE", "SALARY", "PAYSLIP", "EMPLOYER", "GROSS"],
    "address_proof": ["ELECTRICITYBILL", "CONSUMERNO", "RENTAGREEMENT", "BILLDATE"],
}
MIN_PAGE_SIDE_PX = 700  # shorter side of the photo; below this an A4 page is unreadable


def page_sharpness(gray: np.ndarray) -> float:
    """Strength of the sharpest 0.5% of edges on a contrast-normalised, half-size page.

    A4 pages are mostly blank paper, so the card blur score (variance over the whole image) is dominated by
    empty space. The sharpest edges are the printed text, which blur softens directly.
    """
    g = cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA).astype(np.float32)
    g = cv2.GaussianBlur(g, (3, 3), 0)
    g = (g - g.mean()) / max(float(g.std()), 1.0) * 50.0
    return float(np.percentile(np.abs(cv2.Laplacian(g, cv2.CV_32F)), 99.5))


def _hits(doc: str, toks: list[str]) -> int:
    return sum(1 for k in KEYWORDS[doc] if any(fuzz.partial_ratio(k, t) >= 88 for t in toks if len(t) >= 4))


def page_quality(image_bytes: bytes) -> tuple[dict, list[Issue], np.ndarray | None]:
    t = get_thresholds()
    decoded = decode(image_bytes)
    if decoded is None:
        return {"card_found": False, "passed": False}, [make_issue("UNSUPPORTED_FILE", {"detected": "undecodable"})], None
    img, density = decoded
    h, w = img.shape[:2]
    short_side = min(h, w) * density
    scale = 1400 / max(h, w)
    page = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    gray = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
    sharp_min = t.get("page_sharpness_min", 45)
    blur, glare, bright = page_sharpness(gray), glare_fraction(page, t["glare_v"], t["glare_s"]), float(gray.mean())
    issues = []
    if short_side < MIN_PAGE_SIDE_PX:
        issues.append(make_issue("LOW_RESOLUTION", {"page_short_side_px": round(short_side), "threshold": MIN_PAGE_SIDE_PX}))
    if blur < sharp_min:
        issues.append(make_issue("BLUR", {"page_sharpness": round(blur, 1), "threshold": sharp_min}))
    # Paper is white, so only a reflection far larger than on a card counts as glare.
    if glare > 4 * t["glare_blob_frac"] and bright <= t["bright_min"] + 20:
        issues.append(make_issue("GLARE", {"glare_fraction": round(glare, 4), "threshold": 4 * t["glare_blob_frac"]}))
    if bright < t["dark_max"]:
        issues.append(make_issue("TOO_DARK", {"brightness": round(bright, 1), "threshold": t["dark_max"]}))
    passed = not issues
    q = {"card_found": True, "blur_score": round(blur, 1), "glare_fraction": round(glare, 4),
         "brightness": round(bright, 1), "skew_deg": None, "card_width_px": int(round(w * density)), "passed": passed}
    return q, issues, page


def content_check(page: np.ndarray, declared: str) -> tuple[list[Issue], dict, float]:
    """-> (issues, fields, mean OCR confidence)."""
    tokens = ocr.read(page)
    toks = [squash(tk.text) for tk in tokens]
    mean_conf = float(np.mean([tk.conf for tk in tokens])) if tokens else 0.0
    top = [tk for tk in tokens if tk.cy < page.shape[0] * 0.35 and len(squash(tk.text)) >= 5]
    title = max(top, key=lambda tk: tk.h).text.strip() if top else None
    fields = {"title": title}

    id_sc = id_scores(tokens)
    best_id = max(id_sc, key=id_sc.get)
    if id_sc[best_id] >= 3:  # an ID card photographed into a supporting-document slot
        return [make_issue("WRONG_DOC_TYPE", {"declared": declared, "detected": best_id, "score": id_sc[best_id]})], \
            fields, mean_conf
    mine = _hits(declared, toks)
    others = {d: _hits(d, toks) for d in KEYWORDS if d != declared}
    best_other = max(others, key=others.get)
    if mine == 0 and others[best_other] >= 2:
        return [make_issue("WRONG_DOC_TYPE", {"declared": declared, "detected": best_other,
                                              "score": others[best_other]})], fields, mean_conf
    return [make_issue("CONTENT_NOT_VERIFIED", {"keywords_found": mine})], fields, mean_conf
