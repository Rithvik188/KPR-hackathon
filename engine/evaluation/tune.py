"""Tune thresholds on the `tune` split ONLY (background set A). Writes app/validation/thresholds.json.

    python -m evaluation.tune [--refresh]

1. Quality thresholds: per check, maximise F1 for its code subject to a false-retake rate of at most 5%
   on images with no quality problem (a genuine citizen told to retake is a cost).
2. OCR confidence gate: minimise false invalids while keeping INVALID_CHECKSUM recall >= 0.9;
   ties go to the lowest UNREADABLE rate on genuine cards.
3. Name thresholds on the tune document sets.
4. phash duplicate distance from the distribution between *different* cards.

The printed summary is a tuning-split number and is NOT for slides; use evaluation.run (held-out test).
"""
import argparse
import itertools
import json

import numpy as np

from app.validation.quality import quality_codes
from app.validation.thresholds import THRESHOLDS_PATH, get_thresholds
from evaluation.common import CACHE, QUALITY_CODES, load_labels, prf, quality_measures
from evaluation.ocr_cache import ocr_reads, simulate

MAX_FALSE_RETAKE = 0.05

# param(s) -> code, candidate grid
SEARCH = [
    (("blur_min",), "BLUR", [list(range(40, 410, 10))]),
    (("glare_blob_frac",), "GLARE", [list(np.round(np.arange(0.005, 0.0405, 0.0025), 4))]),
    (("dark_max",), "TOO_DARK", [list(range(40, 125, 5))]),
    (("bright_min",), "TOO_BRIGHT", [list(range(180, 240, 5))]),
    (("min_card_width_px",), "LOW_RESOLUTION", [list(range(500, 825, 25))]),
    (("crop_border_px", "crop_aspect_tol", "crop_edge_aspect_tol"), "CROPPED",
     [list(range(2, 16)), list(np.round(np.arange(0.08, 0.32, 0.02), 2)), [0.0, 0.03, 0.05, 0.08, 0.10]]),
]


def _score(code, labels, ms, t):
    tp = fp = fn = 0
    neg = neg_fp = 0
    for lab in labels:
        truth = set(lab["true_codes"]) & set(QUALITY_CODES)
        pred = set(quality_codes(ms[lab["file"]], t))
        if code in truth:
            tp += code in pred
            fn += code not in pred
        else:
            fp += code in pred
        if not truth:
            neg += 1
            neg_fp += code in pred
    p, r, f = prf(tp, fp, fn)
    return f, neg_fp / max(neg, 1), p, r


def tune_quality(labels, ms, t) -> list[str]:
    report = []
    for params, code, grids in SEARCH:
        scored = []
        for combo in itertools.product(*grids):
            cand = {**t, **dict(zip(params, combo))}
            f, fr, p, r = _score(code, labels, ms, cand)
            if fr <= MAX_FALSE_RETAKE:
                scored.append(((round(f, 4), -round(fr, 4)), combo, f, fr, p, r))
        best = None
        if scored:
            top = max(s_[0] for s_ in scored)
            plateau = [s_ for s_ in scored if s_[0] == top]
            best = plateau[len(plateau) // 2]  # middle of the tie plateau = most margin both ways
        if best is None:
            report.append(f"{code:16} no setting meets the false-retake cap; kept {[t[p] for p in params]}")
            continue
        _, combo, f, fr, p, r = best
        for k, v in zip(params, combo):
            t[k] = float(v) if isinstance(v, (float, np.floating)) else int(v)
        report.append(f"{code:16} {dict(zip(params, [t[k] for k in params]))}  F1={f:.3f} P={p:.2f} R={r:.2f} "
                      f"false-retake={fr:.3f}")
    return report


def tune_gate(labels, ocr, t) -> str:
    rows = []
    for gate in np.round(np.arange(0.50, 0.905, 0.01), 2):  # <= ocr_cache.MAX_GATE
        false_invalid = genuine = unreadable = inv_tp = inv_n = 0
        for lab in labels:
            e = ocr.get(lab["file"])
            if not e or not e.get("ran") or set(lab["true_codes"]) & set(QUALITY_CODES):
                continue  # the gate only matters for captures that pass quality
            status, codes, _ = simulate(e, lab["declared_type"], float(gate))
            if lab["number_valid"]:
                genuine += 1
                false_invalid += status == "invalid"
                unreadable += "UNREADABLE" in codes
            if "INVALID_CHECKSUM" in lab["true_codes"]:
                inv_n += 1
                inv_tp += "INVALID_CHECKSUM" in codes
        rows.append((float(gate), false_invalid / max(genuine, 1), inv_tp / max(inv_n, 1), unreadable / max(genuine, 1),
                     false_invalid, genuine, inv_tp, inv_n))
    ok = [r for r in rows if r[2] >= 0.9] or rows
    min_fi = min(r[1] for r in ok)
    ok = [r for r in ok if r[1] == min_fi]
    min_unr = min(r[3] for r in ok)
    # Most conservative gate that costs at most 2 points of extra retakes on genuine cards.
    best = max((r for r in ok if r[3] <= min_unr + 0.02), key=lambda r: r[0])
    t["ocr_min_confidence_for_rules"] = best[0]
    return (f"gate={best[0]:.2f}  false-invalid={best[4]}/{best[5]} ({best[1]:.3f})  "
            f"INVALID_CHECKSUM recall={best[6]}/{best[7]} ({best[2]:.2f})  unreadable(genuine)={best[3]:.3f}")


def _set_docs(split: str, refresh: bool):
    """Extracted docs per set via the real pipeline (cached)."""
    from evaluation.sets import extracted_sets
    return extracted_sets(split, refresh)


def tune_names(t, refresh: bool) -> str:
    from app.validation.consistency import check_consistency

    sets = _set_docs("tune", refresh)
    best = None
    for match_min in range(84, 99, 2):
        for likely_min in range(66, match_min, 4):
            cand = {**t, "name_match_min": match_min, "name_likely_min": likely_min}
            import app.validation.consistency as cons
            orig = cons.get_thresholds
            cons.get_thresholds = lambda c=cand: c
            try:
                correct = sum(check_consistency(docs).name_tier == s["expected_tier"] for s, docs in sets)
            finally:
                cons.get_thresholds = orig
            key = (correct, -abs(match_min - 92))
            if best is None or key > best[0]:
                best = (key, match_min, likely_min, correct)
    _, mm, lm, correct = best
    t["name_match_min"], t["name_likely_min"] = mm, lm
    return f"name_match_min={mm} name_likely_min={lm}  tiers correct {correct}/{len(sets)}"


def tune_phash(labels, ms, t) -> str:
    from app.validation.duplicates import phash_distance

    hashes = [(lab["doc_type"], ms[lab["file"]].get("phash")) for lab in labels if ms[lab["file"]].get("phash")]
    dists = [phash_distance(a[1], b[1]) for a, b in itertools.combinations(hashes, 2) if a[0] == b[0]]
    if not dists:
        return "phash: no data"
    dmin = int(min(dists))
    pct = float(np.percentile(dists, 1))
    # Keep a margin below the closest pair of *different* cards; never above the original 6.
    t["phash_max_distance"] = int(max(-1, min(6, dmin - 4)))
    note = "disabled (different cards too close)" if t["phash_max_distance"] < 2 else "enabled"
    return (f"phash: different same-type cards min distance={dmin}, 1st pct={pct:.0f} -> "
            f"phash_max_distance={t['phash_max_distance']} ({note})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    t = dict(get_thresholds())
    labels = load_labels("tune")
    ms = quality_measures("tune", refresh=a.refresh)
    print("== quality (tune split) ==")
    for line in tune_quality(labels, ms, t):
        print("  " + line)
    print("== OCR confidence gate (tune split) ==")
    print("  " + tune_gate(labels, ocr_reads("tune", refresh=a.refresh), t))
    print("== names (tune sets) ==")
    print("  " + tune_names(t, a.refresh))
    print("== duplicates ==")
    print("  " + tune_phash(labels, ms, t))
    THRESHOLDS_PATH.write_text(json.dumps(t, indent=1) + "\n", encoding="utf-8")
    (CACHE / "tune_summary.json").write_text(json.dumps(t, indent=1))
    print(f"\nwrote {THRESHOLDS_PATH}\n(tune-split numbers above are NOT for slides; run `python -m evaluation.run`)")


if __name__ == "__main__":
    main()
