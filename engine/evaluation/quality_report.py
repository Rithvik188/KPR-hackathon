"""Quick quality-gate check: detected vs true codes with current thresholds.

    python -m evaluation.quality_report --split tune [--refresh] [--show 15]
"""
import argparse
import statistics

from app.validation.quality import quality_codes
from app.validation.thresholds import get_thresholds
from evaluation.common import QUALITY_CODES, load_labels, per_code_scores, quality_measures


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="tune")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--show", type=int, default=15)
    a = ap.parse_args()
    t = get_thresholds()
    labels = load_labels(a.split)
    ms = quality_measures(a.split, refresh=a.refresh)
    pairs, wrong = [], []
    for lab in labels:
        m = ms[lab["file"]]
        truth = set(lab["true_codes"]) & set(QUALITY_CODES)
        pred = set(quality_codes(m, t))
        pairs.append((truth, pred))
        if truth != pred:
            wrong.append((lab["file"], lab["doc_type"], sorted(truth), sorted(pred), lab.get("injected")))
    print(f"{'code':16} {'P':>6} {'R':>6} {'F1':>6} {'sup':>4} {'fp':>4}")
    for s in per_code_scores(pairs, QUALITY_CODES):
        print(f"{s['code']:16} {s['precision']:6.2f} {s['recall']:6.2f} {s['f1']:6.2f} {s['support']:4} {s['fp']:4}")
    clean = [lab for lab in labels if not (set(lab["true_codes"]) & set(QUALITY_CODES))]
    fp_clean = sum(1 for lab in clean if quality_codes(ms[lab["file"]], t))
    print(f"\nclean-quality images flagged (false retake rate): {fp_clean}/{len(clean)}")
    ql = [m.get("quality_ms", 0) for m in ms.values()]
    print(f"quality latency ms p50={statistics.median(ql):.0f} max={max(ql):.0f}")
    print(f"\nmismatches ({len(wrong)}):")
    for w in wrong[: a.show]:
        print("  ", w)
    # measurement distributions per injected type, to see separability
    print("\nmeasure ranges by injected error:")
    groups: dict[str, list[dict]] = {}
    for lab in labels:
        key = "+".join(lab.get("injected") or ["clean"])
        groups.setdefault(key, []).append(ms[lab["file"]])
    for k, g in sorted(groups.items()):
        found = [m for m in g if m.get("card_found")]
        if not found:
            print(f"  {k:22} n={len(g)} card_found=0")
            continue

        def rng(key):
            v = sorted(m[key] for m in found)
            return f"{v[0]:.0f}/{v[len(v) // 2]:.0f}/{v[-1]:.0f}"
        gl = sorted(m["glare"] for m in found)
        print(f"  {k:22} n={len(g):3} found={len(found):3} blur={rng('blur'):16} bright={rng('brightness'):12} "
              f"width={rng('card_width_px'):14} glare={gl[0]:.3f}/{gl[len(gl) // 2]:.3f}/{gl[-1]:.3f} "
              f"edge={rng('edge_dist')}")


if __name__ == "__main__":
    main()
