"""Full e-Aadhaar letter (the A4 PDF citizens download and print) — the most common form brought to a counter.

The page holds the letter, a cut-out front and back card, QR codes, the 16-digit VID, the enrolment number and the
same Aadhaar number printed several times, with Tamil (regional) + English text. This path runs only when the
ID-card path could not find a card-shaped outline.

Rules kept from the card path:
- quality first (no OCR on a blurry or dark page);
- "can't read" is never "invalid": the number must clear the OCR gate, and a failing checksum is only reported
  when two separate printings of the number on the page agree (independent second read);
- the full number is never returned or logged.
"""
import re
from collections import Counter
from dataclasses import dataclass, field

import cv2
import numpy as np

from app.validation import ocr
from app.validation.extract import DATE, clean_name, parse_date
from app.validation.ocr import OcrToken
from app.validation.text import letters, squash

MARKERS = ["UNIQUEIDENTIFICATION", "AUTHORITYOFINDIA", "AADHAAR", "ENROLMENT", "VID", "GOVERNMENTOFINDIA",
           "YOURAADHAARNO", "UIDAI"]
NUM_444 = re.compile(r"(?<![\d ])([2-9]\d{3}) ?(\d{4}) ?(\d{4})(?! ?\d)")  # 4-4-4, not the start of a 4-4-4-4 VID
EXCLUDE_LINE = re.compile(r"VID|ENROL|MOBILE|PHONE|PIN|DATE|ISSUED|DETAILS AS ON|/", re.I)
PIN = re.compile(r"(?<!\d)([1-9]\d{5})(?!\d)")
OCR_SIDE = 2200  # the letter's text is small: OCR at a higher resolution than cards


@dataclass
class PageRead:
    is_letter: bool = False
    markers: int = 0
    numbers: list[tuple[str, float]] = field(default_factory=list)  # every 4-4-4 printing found, with confidence
    name: str | None = None
    dob: str | None = None
    gender: str | None = None
    pin_code: str | None = None
    mean_conf: float = 0.0


def _lines(tokens: list[OcrToken]) -> list[list[OcrToken]]:
    out: list[list[OcrToken]] = []
    for t in sorted(tokens, key=lambda t: t.cy):
        for ln in out:
            if abs(t.cy - ln[0].cy) < 0.5 * max(min(t.h, ln[0].h), 1) and abs(t.bbox[0] - ln[-1].bbox[2]) < 400:
                ln.append(t)
                break
        else:
            out.append([t])
    return [sorted(ln, key=lambda t: t.bbox[0]) for ln in out]


def _latin_ratio(s: str) -> float:
    chars = [c for c in s if not c.isspace()]
    return sum(c.isascii() for c in chars) / len(chars) if chars else 0.0


def read_page(img_bgr: np.ndarray) -> PageRead:
    h, w = img_bgr.shape[:2]
    scale = OCR_SIDE / max(h, w)
    page = cv2.resize(img_bgr, (round(w * scale), round(h * scale)),
                      interpolation=cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC)
    tokens = ocr.read(page)
    r = PageRead(mean_conf=float(np.mean([t.conf for t in tokens])) if tokens else 0.0)
    sq = " ".join(squash(t.text) for t in tokens)
    r.markers = sum(1 for m in MARKERS if m in sq)

    lns = _lines(tokens)
    texts = [" ".join(t.text for t in ln) for ln in lns]
    for ln, text in zip(lns, texts):
        if EXCLUDE_LINE.search(text):
            continue
        normalised = re.sub(r"[Oo]", "0", text)
        for m in NUM_444.finditer(normalised):
            digits = "".join(m.groups())
            conf = min((t.conf for t in ln if any(ch.isdigit() for ch in t.text)), default=0.0)
            r.numbers.append((digits, conf))
    if r.numbers and Counter(n for n, _ in r.numbers).most_common(1)[0][1] >= 2:
        r.markers += 1  # the same number printed twice is itself a strong e-Aadhaar marker
    r.is_letter = r.markers >= 2 and bool(r.numbers)

    # Name: the Latin-script token just above the DOB token, in the same column (the Tamil name sits above it and
    # is skipped; the back card's "Address" can sit at the same height in the other column).
    dob_tok = next((t for t in tokens if "DOB" in t.text.upper() and DATE.search(t.text.replace(" ", ""))), None) or         next((t for t in tokens if "DOB" in t.text.upper()), None)
    if dob_tok is not None:
        r.dob = parse_date(dob_tok.text) or next((parse_date(t.text) for t in tokens
                                                  if abs(t.cy - dob_tok.cy) < dob_tok.h and parse_date(t.text)), None)
        above = [t for t in tokens if 0 < dob_tok.cy - t.cy < 6 * max(dob_tok.h, 10)
                 and abs(t.bbox[0] - dob_tok.bbox[0]) < 3 * max(dob_tok.h, 10)
                 and _latin_ratio(t.text) > 0.9 and 3 <= len(letters(t.text)) <= 40
                 and not re.search(r"GOVERNMENT|INDIA|AUTHORITY|AADHAAR|ISSUED|ENROL|VID|ADDRESS|TO|\d",
                                   t.text.upper())]
        if above:
            r.name = clean_name(max(above, key=lambda t: t.cy).text)
    for text in texts:
        up = text.upper()
        if r.gender is None and re.search(r"\bFEMALE\b", up):
            r.gender = "F"
        elif r.gender is None and re.search(r"\bMALE\b", up):
            r.gender = "M"
        if r.pin_code is None and ("PIN" in up or re.search(r"TAMIL\s*NADU", up)):
            m = PIN.search(re.sub(r"\s", "", text))
            if m:
                r.pin_code = m.group(1)
    return r


def best_number(r: PageRead) -> tuple[str | None, float | None, tuple[str, float] | None]:
    """Most-repeated 4-4-4 number, its best confidence, and an independent second printing (if any)."""
    if not r.numbers:
        return None, None, None
    counts = Counter(n for n, _ in r.numbers)
    number, _ = counts.most_common(1)[0]
    confs = sorted((c for n, c in r.numbers if n == number), reverse=True)
    second = (number, confs[1]) if len(confs) >= 2 else None
    return number, confs[0], second
