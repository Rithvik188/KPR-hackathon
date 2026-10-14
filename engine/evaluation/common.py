"""Shared evaluation helpers: labels, cached per-image measurements, scoring."""
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
DATA = ENGINE / "datagen" / "out"
CACHE = ENGINE / "evaluation" / "cache"

QUALITY_CODES = ["CARD_NOT_FOUND", "CROPPED", "BLUR", "GLARE", "TOO_DARK", "TOO_BRIGHT", "LOW_RESOLUTION"]


def load_labels(split: str) -> list[dict]:
    path = DATA / split / "labels.jsonl"
    if not path.exists():
        raise SystemExit(f"{path} missing: run `python -m datagen.generate --split {split}` first")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _measure_one(path: str) -> dict:
    from app.validation.api import _phash
    from app.validation.quality import measure

    data = Path(path).read_bytes()
    t0 = time.perf_counter()
    m, card = measure(data)
    m["quality_ms"] = (time.perf_counter() - t0) * 1000
    m["phash"] = _phash(card) if card is not None else None
    return m


def quality_measures(split: str, refresh: bool = False, workers: int = 6) -> dict[str, dict]:
    """file -> raw quality measurements. Cached; re-measured only with refresh=True."""
    CACHE.mkdir(parents=True, exist_ok=True)
    cache = CACHE / f"{split}_quality.json"
    labels = load_labels(split)
    if cache.exists() and not refresh:
        data = json.loads(cache.read_text())
        if all(lab["file"] in data for lab in labels):
            return data
    paths = [str(DATA / split / lab["file"]) for lab in labels]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        ms = list(ex.map(_measure_one, paths, chunksize=4))
    data = {lab["file"]: m for lab, m in zip(labels, ms)}
    cache.write_text(json.dumps(data))
    return data


def prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def per_code_scores(pairs: list[tuple[set, set]], codes: list[str]) -> list[dict]:
    """pairs = [(true_codes, predicted_codes)] -> P/R/F1/support per code."""
    out = []
    for c in codes:
        tp = sum(1 for t, p in pairs if c in t and c in p)
        fp = sum(1 for t, p in pairs if c not in t and c in p)
        fn = sum(1 for t, p in pairs if c in t and c not in p)
        support = tp + fn
        if support == 0 and fp == 0:
            continue
        p, r, f = prf(tp, fp, fn)
        out.append({"code": c, "precision": round(p, 3), "recall": round(r, 3), "f1": round(f, 3),
                    "support": support, "fp": fp})
    return out
