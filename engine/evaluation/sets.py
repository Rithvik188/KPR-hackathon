"""Extracted documents for the consistency sets (real pipeline, cached)."""
import json
from concurrent.futures import ProcessPoolExecutor

from evaluation.common import CACHE, DATA

SETS = DATA / "sets"


def load_sets(split: str) -> list[dict]:
    path = SETS / split / "sets.jsonl"
    if not path.exists():
        raise SystemExit(f"{path} missing: run `python -m datagen.generate_sets` first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _extract_one(args: tuple[str, str]) -> dict | None:
    from app.validation.api import validate_image

    path, declared = args
    out = validate_image(open(path, "rb").read(), declared)
    ex = out.extracted
    return {"status": out.result.status, "extracted": ex.to_dict() if ex else None}


def extracted_sets(split: str, refresh: bool = False, workers: int = 6):
    """-> [(set_row, [ExtractedDoc...])] using only documents the engine accepted or extracted."""
    from app.validation.types import ExtractedDoc

    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"sets_{split}.json"
    rows = load_sets(split)
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text())
    else:
        jobs, keys = [], []
        for r in rows:
            for doc_type, d in r["docs"].items():
                jobs.append((str(SETS / split / d["file"]), doc_type))
                keys.append(d["file"])
        with ProcessPoolExecutor(max_workers=workers) as ex:
            res = list(ex.map(_extract_one, jobs, chunksize=2))
        data = dict(zip(keys, res))
        cache.write_text(json.dumps(data))
    out = []
    for r in rows:
        docs = []
        for d in r["docs"].values():
            e = data.get(d["file"])
            if e and e["extracted"]:
                docs.append(ExtractedDoc.from_dict(e["extracted"]))
        out.append((r, docs))
    return out
