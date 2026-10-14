"""Cached OCR reads per image so threshold search runs on numbers, not on OCR.

For every image that passes the quality gate we store: classification, the first read of the ID number,
the 1.5x retry read and the 1.3x second read (number + confidence each), plus extracted fields.
`simulate()` replays validate_image's decision logic for any gate value.
Cache files live in evaluation/cache/ (gitignored; synthetic numbers only).
"""
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from evaluation.common import CACHE, DATA, load_labels

MAX_GATE = 0.90
EMPTY = {"number": None, "conf": None, "subs": 0, "name": None, "dob": None, "gender": None, "father": None,
         "pin": None}


def _ocr_one(args: tuple[str, str | None]) -> dict:
    path, declared = args
    from app.validation.api import _ocr_and_classify, _scaled_read
    from app.validation.extract import extract
    from app.validation.quality import assess
    from app.validation.thresholds import get_thresholds

    t = get_thresholds()
    rep = assess(Path(path).read_bytes())
    if rep.card is None:  # OCR every found card; tune_gate only scores quality-clean images
        return {"ran": False}
    card, tokens, detected, scores = _ocr_and_classify(rep.card, declared, t["classify_min_score"])
    out = {"ran": True, "detected": detected, "scores": scores}
    if detected == "unknown":
        return out
    from app.validation.rules import check_number

    ex1 = extract(detected, tokens)
    reads = [("r1", ex1)]
    # Only compute the extra reads the decision logic can actually use (gate grid tops out at MAX_GATE).
    ex2 = None
    if not ex1.id_number or (ex1.id_confidence or 0) < MAX_GATE:
        ex2 = _scaled_read(card, detected, 1.5)
        reads.append(("r15", ex2))
    if any(e is not None and e.id_number and check_number(detected, e.id_number) for e in (ex1, ex2)):
        reads.append(("r13", _scaled_read(card, detected, 1.3)))
    for k, ex in reads:
        out[k] = {"number": ex.id_number, "conf": ex.id_confidence, "subs": ex.id_subs, "name": ex.name,
                  "dob": ex.dob, "gender": ex.gender, "father": ex.father_name, "pin": ex.pin_code}
    return out


def ocr_reads(split: str, refresh: bool = False, workers: int = 3) -> dict[str, dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{split}_ocr.json"
    labels = load_labels(split)
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text())
        if all(lab["file"] in data for lab in labels):
            return data
    from evaluation.common import QUALITY_CODES

    # Gate tuning only scores captures without a true quality defect, so only those need OCR.
    todo = [lab for lab in labels if not set(lab["true_codes"]) & set(QUALITY_CODES)]
    jobs = [(str(DATA / split / lab["file"]), lab["declared_type"]) for lab in todo]
    res = []
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for i, r in enumerate(ex.map(_ocr_one, jobs, chunksize=1), 1):
            res.append(r)
            if i % 25 == 0 or i == len(jobs):
                print(f"  ocr {split}: {i}/{len(jobs)}", flush=True)
    data = {lab["file"]: {"ran": False} for lab in labels}
    data.update({lab["file"]: r for lab, r in zip(todo, res)})
    cache.write_text(json.dumps(data))
    return data


def simulate(entry: dict, declared: str | None, gate: float) -> tuple[str, list[str], dict | None]:
    """Replay validate_image's post-OCR logic -> (status, codes, chosen read)."""
    from app.validation.rules import apply_rules
    from app.validation.types import doc_status

    if not entry.get("ran"):
        return "skip", [], None
    det = entry["detected"]
    if det == "unknown":
        return "fixable", ["UNKNOWN_DOC_TYPE"], None
    if declared and det != declared:
        return "fixable", ["WRONG_DOC_TYPE"], None
    r = entry["r1"]
    if not r["number"] or (r["conf"] or 0) < gate:
        r2 = entry.get("r15", EMPTY)
        if r2["number"] and (r2["conf"] or 0) > (r["conf"] or 0):
            r = {**r2, "name": r2["name"] or r["name"], "dob": r2["dob"] or r["dob"]}
    second = entry.get("r13", EMPTY)
    rr = apply_rules(det, r["number"], r["conf"], r["subs"], gate,
                     lambda: (second["number"], second["conf"]))
    issues = rr.issues or []
    status = doc_status(issues) if issues else "accepted"
    return status, [i.code for i in issues], {**r, "number": rr.number}
