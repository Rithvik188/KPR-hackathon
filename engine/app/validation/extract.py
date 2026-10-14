"""Per-type field extraction from OCR tokens (regex + positional heuristics).

Returns the raw ID number (never logged), its OCR confidence and the token boxes it came from,
so rules.py can apply the confidence gate and re-read the number if needed.
"""
import re
from dataclasses import dataclass, field
from datetime import date

from rapidfuzz import fuzz

from app.validation.ocr import OcrToken
from app.validation.text import (clean_name, correct_pattern, digit_ratio, letters, respace, squash,
                                 to_digits)

DATE = re.compile(r"(\d{2})[/\-.](\d{2})[/\-.](\d{4})")
PIN = re.compile(r"(?<!\d)([1-9]\d{5})(?!\d)")
WATERMARK = "SPECIMENNOTAREALDOCUMENT"
LABEL_WORDS = ["GOVERNMENT", "INDIA", "DOB", "MALE", "FEMALE", "ADDRESS", "NAME", "FATHER", "DATE", "BIRTH",
               "INCOME", "TAX", "DEPARTMENT", "PERMANENT", "ACCOUNT", "ELECTION", "COMMISSION", "ELECTOR",
               "IDENTITY", "CARD", "SEX", "UNIQUE", "AUTHORITY"]


@dataclass
class Extracted:
    id_number: str | None = None  # raw, unmasked: never log or return
    id_confidence: float | None = None
    id_subs: int = 0  # confusable substitutions made
    id_boxes: list[tuple[float, float, float, float]] = field(default_factory=list)
    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    father_name: str | None = None
    pin_code: str | None = None


def is_watermark(t: OcrToken) -> bool:
    s = squash(t.text)
    return len(s) >= 6 and (fuzz.partial_ratio(s, WATERMARK) >= 75 or "SPECIMEN" in s or "REALDOC" in s)


def lines(tokens: list[OcrToken]) -> list[list[OcrToken]]:
    """Group tokens into text lines by vertical overlap."""
    out: list[list[OcrToken]] = []
    for t in sorted(tokens, key=lambda t: t.cy):
        for ln in out:
            ref = ln[0]
            if abs(t.cy - ref.cy) < 0.5 * max(min(t.h, ref.h), 1):
                ln.append(t)
                break
        else:
            out.append([t])
    return [sorted(ln, key=lambda t: t.bbox[0]) for ln in out]


_DATE_FIX = str.maketrans("OIlLSBZ", "0111582")


def parse_date(text: str) -> str | None:
    """dd/mm/yyyy anywhere in the text -> ISO, tolerating confusables inside the date."""
    raw = re.sub(r"\s", "", text or "")
    for cand in (raw, raw.translate(_DATE_FIX)):
        for m in DATE.finditer(cand):
            d, mth, y = map(int, m.groups())
            try:
                if 1900 <= y <= date.today().year:
                    return date(y, mth, d).isoformat()
            except ValueError:
                continue
    return None


def _is_label(text: str) -> bool:
    s = letters(text)
    return any(w in s for w in LABEL_WORDS)


def _name_like(text: str) -> bool:
    s = letters(text)
    return len(s) >= 3 and digit_ratio(text) < 0.1 and not _is_label(text)


def _after_colon(text: str) -> str | None:
    if ":" in text:
        tail = text.split(":", 1)[1].strip()
        return tail or None
    return None


def _value_below(tokens: list[OcrToken], label: OcrToken, max_dy: float = 80) -> OcrToken | None:
    cands = [t for t in tokens if t is not label and 0 < t.cy - label.cy <= max_dy and abs(t.bbox[0] - label.bbox[0]) < 120]
    return min(cands, key=lambda t: t.cy - label.cy) if cands else None


def _value_right(line: list[OcrToken], label: OcrToken) -> OcrToken | None:
    right = [t for t in line if t.bbox[0] > label.bbox[2] - 5 and t is not label]
    return right[0] if right else None


def _find(tokens: list[OcrToken], *keywords: str, min_ratio: int = 85) -> OcrToken | None:
    for t in tokens:
        s = letters(t.text)
        if all(fuzz.partial_ratio(k, s) >= min_ratio for k in keywords):
            return t
    return None


def _aadhaar_number(lns: list[list[OcrToken]]) -> tuple[str | None, float | None, int, list]:
    """Bottom-most line holding exactly 12 digits (digit-like tokens joined across the line)."""
    for ln in reversed(lns):
        parts = [t for t in ln if digit_ratio(t.text) >= 0.6]
        if not parts:
            continue
        digits, subs = to_digits("".join(t.text for t in parts))
        m = re.search(r"(?<!\d)([2-9]?\d{11,12})(?!\d)", digits)
        if len(digits) == 12 or (m and len(m.group(1)) == 12):
            return digits[-12:] if len(digits) == 12 else m.group(1), min(t.conf for t in parts), subs, \
                [t.bbox for t in parts]
        if 10 <= len(digits) <= 14:  # present but mis-read length -> rules decide (INVALID_FORMAT / UNREADABLE)
            return digits, min(t.conf for t in parts), subs, [t.bbox for t in parts]
    return None, None, 0, []


def _patterned(tokens: list[OcrToken], pattern: str) -> tuple[str | None, float | None, int, list]:
    """Best token matching a letter/digit pattern such as 'AAAAA9999A' (PAN) or 'AAA9999999' (EPIC)."""
    best = None
    for t in tokens:
        raw = squash(t.text)
        if not (len(pattern) - 1 <= len(raw) <= len(pattern) + 1):
            continue
        fixed, subs = correct_pattern(raw, pattern)
        shape = sum(1 for ch, k in zip(fixed, pattern) if (k == "9") == ch.isdigit())
        if shape >= len(pattern) - 2 and (best is None or (shape, t.conf) > (best[0], best[1].conf)):
            best = (shape, t, fixed, subs)
    if best is None:
        return None, None, 0, []
    return best[2], best[1].conf, best[3], [best[1].bbox]


def extract(doc_type: str, tokens: list[OcrToken]) -> Extracted:
    tokens = [t for t in tokens if not is_watermark(t)]
    lns = lines(tokens)
    out = Extracted()
    upper_all = " ".join(t.text.upper() for t in tokens)

    if doc_type in ("aadhaar_front", "aadhaar_back"):
        out.id_number, out.id_confidence, out.id_subs, out.id_boxes = _aadhaar_number(lns)
    elif doc_type == "pan":
        out.id_number, out.id_confidence, out.id_subs, out.id_boxes = _patterned(tokens, "AAAAA9999A")
    elif doc_type == "voter_id":
        out.id_number, out.id_confidence, out.id_subs, out.id_boxes = _patterned(tokens, "AAA9999999")

    if doc_type == "aadhaar_front":
        dob_tok = next((t for t in tokens if "DOB" in squash(t.text) or DATE.search(t.text)), None)
        if dob_tok:
            out.dob = parse_date(dob_tok.text)
            above = [t for t in tokens if t.cy < dob_tok.cy - 5 and _name_like(t.text) and t.cy > 110]
            if above:
                out.name = clean_name(max(above, key=lambda t: t.cy).text)
        out.gender = "F" if "FEMALE" in upper_all.replace(" ", "") else ("M" if "MALE" in upper_all else None)

    elif doc_type == "aadhaar_back":
        for ln in lns:
            text = " ".join(t.text for t in ln)
            if digit_ratio(text) > 0.8:
                continue  # the Aadhaar number line
            m = PIN.search(re.sub(r"\s", "", text))
            if m:
                out.pin_code = m.group(1)

    elif doc_type == "pan":
        name_lbl = next((t for t in tokens if letters(t.text) == "NAME" or
                         (fuzz.ratio(letters(t.text), "NAME") >= 75 and len(letters(t.text)) <= 5)), None)
        father_lbl = _find(tokens, "FATHER")
        dob_lbl = _find(tokens, "DATEOFBIRTH", min_ratio=80)
        father_tok = _value_below(tokens, father_lbl) if father_lbl else None
        if father_tok and _name_like(father_tok.text):
            out.father_name = clean_name(father_tok.text)
        name_tok = _value_below(tokens, name_lbl) if name_lbl else None
        if name_tok and _name_like(name_tok.text):
            out.name = respace(name_tok.text, out.father_name)
        dob_src = _value_below(tokens, dob_lbl) if dob_lbl else None
        out.dob = parse_date(dob_src.text) if dob_src else None
        if not out.dob:
            out.dob = next((d for d in (parse_date(t.text) for t in tokens) if d), None)

    elif doc_type == "voter_id":
        def field_value(*kw: str) -> str | None:
            lbl = _find(tokens, *kw, min_ratio=80)
            if not lbl:
                return None
            v = _after_colon(lbl.text)
            if v:
                return v
            ln = next((ln for ln in lns if lbl in ln), [])
            nxt = _value_right(ln, lbl)
            return nxt.text.lstrip(": ") if nxt else None

        father = field_value("FATHER")
        if father and _name_like(father):
            out.father_name = clean_name(father)
        name = field_value("ELECTOR", "NAME")
        if name and letters(name):
            out.name = respace(name, out.father_name)
        sex = field_value("SEX")
        if sex:
            out.gender = "F" if "FEMALE" in letters(sex) else ("M" if "MALE" in letters(sex) else None)
        dob = field_value("BIRTH")
        out.dob = parse_date(dob) if dob else next((d for d in (parse_date(t.text) for t in tokens) if d), None)

    if doc_type == "aadhaar_front" and out.name:
        out.name = clean_name(out.name)
    return out
