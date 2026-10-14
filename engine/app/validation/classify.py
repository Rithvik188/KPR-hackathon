"""Document type from OCR text: fuzzy keyword scoring + ID-number patterns."""
import re

from rapidfuzz import fuzz

from app.validation.ocr import OcrToken
from app.validation.text import squash

KEYWORDS = {
    "aadhaar_front": ["GOVERNMENTOFINDIA", "DOB", "MALE", "YEAROFBIRTH"],
    "aadhaar_back": ["UNIQUEIDENTIFICATION", "AUTHORITYOFINDIA", "ADDRESS"],
    "pan": ["INCOMETAXDEPARTMENT", "PERMANENTACCOUNT", "ACCOUNTNUMBERCARD"],
    "voter_id": ["ELECTIONCOMMISSION", "ELECTORPHOTO", "IDENTITYCARD", "ELECTORSNAME"],
}
PATTERNS = {
    "aadhaar_front": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "aadhaar_back": re.compile(r"(?<!\d)\d{12}(?!\d)"),
    "pan": re.compile(r"[A-Z]{5}\d{4}[A-Z]"),
    "voter_id": re.compile(r"(?<![A-Z])[A-Z]{3}\d{7}(?!\d)"),
}
PIN = re.compile(r"(?<!\d)6\d{5}(?!\d)")


def _hit(keyword: str, tokens: list[str]) -> bool:
    if len(keyword) <= 4:  # short words must appear as (part of) a token exactly
        return any(keyword in t for t in tokens)
    return any(fuzz.partial_ratio(keyword, t) >= 85 for t in tokens if len(t) >= len(keyword) * 0.6)


def scores(tokens: list[OcrToken]) -> dict[str, float]:
    sq = [squash(t.text) for t in tokens]
    joined = " ".join(sq)
    nospace_digits = " ".join(re.sub(r"\s", "", t.text.upper()) for t in tokens)
    out = {}
    for doc, kws in KEYWORDS.items():
        s = sum(1.0 for k in kws if _hit(k, sq))
        if PATTERNS[doc].search(joined) or PATTERNS[doc].search(nospace_digits):
            s += 1.0
        out[doc] = s
    if PIN.search(joined.replace("TAMILNADU", " ")):
        out["aadhaar_back"] += 0.5
    if out["aadhaar_back"] >= 2:  # "AUTHORITY OF INDIA" also fuzzily resembles the front header
        out["aadhaar_front"] -= 0.5
    return out


def classify(tokens: list[OcrToken], declared_type: str | None, min_score: float) -> tuple[str, dict[str, float]]:
    sc = scores(tokens)
    best = max(sc.values())
    if best < min_score:
        return "unknown", sc
    tied = [d for d, v in sc.items() if v == best]
    if declared_type in tied:
        return declared_type, sc
    return tied[0], sc
