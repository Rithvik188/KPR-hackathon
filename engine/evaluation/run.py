"""Held-out evaluation on the `test` split and test sets ONLY (background set B, never used for tuning).

    python -m evaluation.run [--latency-n 40]

Writes evaluation/results.json (DetectionMetrics contract shape, source="evaluation") and
evaluation/report.md (human-readable, with the worst failures by file name).
"""
import argparse
import json
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from rapidfuzz import fuzz

from evaluation.common import DATA, ENGINE, QUALITY_CODES, load_labels, per_code_scores
from evaluation.sets import extracted_sets, load_sets

OUT_JSON = ENGINE / "evaluation" / "results.json"
OUT_MD = ENGINE / "evaluation" / "report.md"
INFO_CODES = {"SKEW_CORRECTED", "OCR_AUTOCORRECTED", "DUPLICATE_SUSPECTED"}
TIERS = ["match", "likely_match", "mismatch"]


def _run_one(args: tuple[str, str]) -> dict:
    from app.validation.api import validate_image

    path, declared = args
    out = validate_image(Path(path).read_bytes(), declared)
    r = out.result
    return {"status": r.status, "doc_type": r.doc_type, "codes": [i.code for i in r.issues],
            "fields": r.fields, "timings": r.timings_ms.model_dump(), "ocr_ran": r.ocr is not None,
            "hmac": out.aadhaar_hmac}


def _letters(s: str | None) -> str:
    return "".join(c for c in (s or "").upper() if c.isalpha())


def pct(xs: list[float], p: float) -> int:
    if not xs:
        return 0
    xs = sorted(xs)
    return int(round(xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))]))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--latency-n", type=int, default=40)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    from app.core.security import aadhaar_hmac
    from app.validation.consistency import check_consistency

    labels = load_labels("test")
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        preds = list(ex.map(_run_one, [(str(DATA / "test" / lab["file"]), lab["declared_type"]) for lab in labels],
                            chunksize=2))
    print(f"validated {len(labels)} test images in {time.time() - t0:.0f}s")

    # ---- per-code detection ----
    scored_codes = sorted({c for lab in labels for c in lab["true_codes"]},
                          key=lambda c: (QUALITY_CODES + ["WRONG_DOC_TYPE", "INVALID_CHECKSUM"]).index(c)
                          if c in QUALITY_CODES + ["WRONG_DOC_TYPE", "INVALID_CHECKSUM"] else 99)
    pairs = [(set(lab["true_codes"]), set(p["codes"]) - INFO_CODES) for lab, p in zip(labels, preds)]
    per_code = per_code_scores(pairs, scored_codes)

    # ---- doc type (images with no quality error) ----
    q_clean = [(lab, p) for lab, p in zip(labels, preds) if not set(lab["true_codes"]) & set(QUALITY_CODES)]
    dt_ok = sum(p["doc_type"] == lab["doc_type"] for lab, p in q_clean)
    doc_type_accuracy = dt_ok / max(len(q_clean), 1)

    # ---- fields (quality-clean, correctly-declared images; a retake counts as a miss) ----
    acc = {"aadhaar_number": [], "pan_number": [], "epic_number": [], "dob": [], "name": []}
    for lab, p in q_clean:
        if "WRONG_DOC_TYPE" in lab["true_codes"]:
            continue
        tr, f = lab["truth"], p["fields"] or {}
        dt = lab["doc_type"]
        if dt.startswith("aadhaar") and lab["number_valid"]:
            acc["aadhaar_number"].append(p["hmac"] is not None and p["hmac"] == aadhaar_hmac(tr["id_number"]))
        elif dt == "pan":
            acc["pan_number"].append(f.get("id_number_display") == tr["id_number"])
        elif dt == "voter_id":
            acc["epic_number"].append(f.get("id_number_display") == tr["id_number"])
        if tr.get("dob"):
            acc["dob"].append(f.get("dob") == tr["dob"])
        if tr.get("name"):
            acc["name"].append(fuzz.ratio(_letters(f.get("name")), _letters(tr["name"])) >= 95)
    field_accuracy = {k: round(sum(v) / len(v), 3) if v else 0.0 for k, v in acc.items()}
    field_support = {k: len(v) for k, v in acc.items()}

    # ---- false invalids: the key trust metric ----
    genuine = [(lab, p) for lab, p in zip(labels, preds) if lab["number_valid"]]
    false_invalid = [(lab, p) for lab, p in genuine if p["status"] == "invalid"]
    false_invalid_rate = len(false_invalid) / max(len(genuine), 1)
    clean_genuine = [(lab, p) for lab, p in genuine if not lab["true_codes"]]
    accepted_clean = sum(p["status"] == "accepted" for _, p in clean_genuine) / max(len(clean_genuine), 1)

    # ---- latency: measured sequentially in this process (no parallel load) ----
    from app.validation.api import validate_image
    from app.validation.ocr import get_reader

    get_reader()
    q_lat, f_lat = [], []
    for lab in labels[: a.latency_n]:
        data = (DATA / "test" / lab["file"]).read_bytes()
        r = validate_image(data, lab["declared_type"]).result
        q_lat.append(r.timings_ms.quality)  # the quality gate (the whole response when it rejects)
        if r.ocr is not None:
            f_lat.append(r.timings_ms.total)
    latency = {"quality_p50": pct(q_lat, 50), "quality_p95": pct(q_lat, 95),
               "full_p50": pct(f_lat, 50), "full_p95": pct(f_lat, 95)}

    # ---- consistency on held-out test sets ----
    sets = extracted_sets("test", refresh=True, workers=a.workers)
    confusion = [[0, 0, 0] for _ in TIERS]
    ned, back_ok, back_n, cons_fail = 0, 0, 0, []
    for row, docs in sets:
        res = check_consistency(docs)
        if row["back_missing"]:
            back_n += 1
            back_ok += any(i.code == "AADHAAR_BACK_MISSING" for i in res.issues)
        if res.name_tier == "not_enough_data":
            ned += 1
            cons_fail.append((row["set"], row["expected_tier"], "not_enough_data"))
            continue
        confusion[TIERS.index(row["expected_tier"])][TIERS.index(res.name_tier)] += 1
        if res.name_tier != row["expected_tier"]:
            cons_fail.append((row["set"], row["expected_tier"], res.name_tier))

    results = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "evaluation",
        "dataset": {"tune_n": len(load_labels("tune")), "test_n": len(labels),
                    "sets_n": len(load_sets("tune")) + len(load_sets("test")),
                    "note_en": "Held-out synthetic SPECIMEN captures with simulated phone-camera degradation "
                               "(test split uses backgrounds never seen during tuning). Not yet validated on "
                               "real-world captures."},
        "per_code": [{k: s[k] for k in ("code", "precision", "recall", "f1", "support")} for s in per_code],
        "doc_type_accuracy": round(doc_type_accuracy, 3),
        "field_accuracy": field_accuracy,
        "false_invalid_rate": round(false_invalid_rate, 4),
        "latency_ms": latency,
        "consistency": {"labels": TIERS, "confusion": confusion},
    }
    OUT_JSON.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")

    # ---- report.md ----
    worst = []
    for lab, p in zip(labels, preds):
        truth, pred = set(lab["true_codes"]), set(p["codes"]) - INFO_CODES
        if truth != pred:
            sev = 3 if (lab["number_valid"] and p["status"] == "invalid") else (
                2 if truth - pred else 1)  # false invalid > missed problem > extra flag
            worst.append((sev, lab["file"], lab["doc_type"], sorted(truth), sorted(pred), p["status"]))
    worst.sort(key=lambda w: -w[0])
    lines = [
        "# SevaiCheck held-out evaluation", "",
        f"Generated {results['generated_at']} on the **test split only** ({len(labels)} images, background set B) "
        f"and {len(sets)} held-out document sets. Thresholds were tuned on a separate split (background set A).", "",
        "## Key trust metric", "",
        f"- **False-invalid rate: {false_invalid_rate:.2%}** ({len(false_invalid)} of {len(genuine)} genuine cards "
        f"were marked `invalid`).",
        f"- Clean genuine cards accepted first time: {accepted_clean:.1%} ({len(clean_genuine)} cards).", "",
        "## Detection per code", "", "| Code | Precision | Recall | F1 | Support | False flags |", "|---|---|---|---|---|---|",
        *[f"| {s['code']} | {s['precision']:.2f} | {s['recall']:.2f} | {s['f1']:.2f} | {s['support']} | {s['fp']} |"
          for s in per_code], "",
        f"Document-type accuracy (images without quality errors): **{doc_type_accuracy:.1%}** (n={len(q_clean)})", "",
        "## Field accuracy", "", "| Field | Accuracy | n |", "|---|---|---|",
        *[f"| {k} | {v:.1%} | {field_support[k]} |" for k, v in field_accuracy.items()], "",
        "Names are compared ignoring spaces (rapidfuzz ratio >= 95 on letters only), because the OCR engine often "
        "drops word spaces. Aadhaar numbers are compared via their HMAC, so the engine never has to return them. "
        "A retake request counts as a miss.", "",
        "## Latency (sequential, single process)", "",
        f"- Quality gate: p50 {latency['quality_p50']} ms, p95 {latency['quality_p95']} ms",
        f"- Full validation (quality + OCR + rules): p50 {latency['full_p50']} ms, p95 {latency['full_p95']} ms", "",
        "## Consistency (held-out sets)", "", "| expected \\ predicted | match | likely_match | mismatch |",
        "|---|---|---|---|",
        *[f"| {TIERS[i]} | {r[0]} | {r[1]} | {r[2]} |" for i, r in enumerate(confusion)], "",
        f"- Sets with too little readable data (`not_enough_data`, excluded above): {ned}",
        f"- `AADHAAR_BACK_MISSING` raised on {back_ok}/{back_n} sets missing the back.", "",
        "## Worst failures (up to 10)", "", "| File | Doc | True codes | Predicted | Status |", "|---|---|---|---|---|",
        *[f"| {w[1]} | {w[2]} | {', '.join(w[3]) or '-'} | {', '.join(w[4]) or '-'} | {w[5]} |" for w in worst[:10]],
        "", *(["Consistency misses: " + "; ".join(f"{s} expected {e}, got {g}" for s, e, g in cons_fail[:10])]
              if cons_fail else []), "",
        "## Honest limitations", "",
        "- All data is synthetic (SPECIMEN cards rendered by us). Templates, fonts and degradations are our "
        "simulation, so these numbers say how well the checks separate *our* simulated failure modes.",
        "- Scores near 100% (e.g. LOW_RESOLUTION, GLARE) mostly mean the simulated defect is easy to separate; real "
        "phone captures will be harder. The next step is a pilot with real-capture validation.",
        "- Support per code is small (about 20-40 images), so each percentage point is roughly one image.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: results[k] for k in ("doc_type_accuracy", "field_accuracy", "false_invalid_rate",
                                              "latency_ms")}, indent=1))
    for s in per_code:
        print(f"  {s['code']:16} P={s['precision']:.2f} R={s['recall']:.2f} F1={s['f1']:.2f} n={s['support']}")
    print("consistency", confusion, "ned", ned, f"back-missing {back_ok}/{back_n}")
    print(f"wrote {OUT_JSON} and {OUT_MD}")


if __name__ == "__main__":
    main()
