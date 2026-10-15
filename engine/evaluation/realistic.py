"""Realistic-layout check: synthetic documents laid out like the REAL current designs (e-Aadhaar letter, bilingual
PAN card and e-PAN printout), never used for tuning. Reported separately from the main held-out evaluation.

    python -m evaluation.realistic [--n 40]

Writes datagen/out/realistic/ (images + labels.jsonl) and evaluation/realistic.json.
"""
import argparse
import json
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from evaluation.common import DATA, ENGINE

OUT = DATA / "realistic"
RESULT = ENGINE / "evaluation" / "realistic.json"


def _make(i: int) -> dict:
    from datagen.capture import CaptureSpec, capture
    from datagen.eaadhaar import render_eaadhaar
    from datagen.epan import render_epan_printout, render_pan_card
    from datagen.identities import make_person
    from datagen.numbers import make_aadhaar, make_pan

    rng = random.Random(7700 + i)
    p = make_person(rng)
    kind = ["eaadhaar_front", "eaadhaar_back", "pan_card", "epan_printout"][i % 4]
    if kind.startswith("eaadhaar"):
        number = make_aadhaar(rng)
        img = render_eaadhaar(p, number, "".join(str(rng.randint(0, 9)) for _ in range(16)), rng)
        spec = CaptureSpec(card_width=rng.uniform(780, 860), rotation_deg=rng.uniform(-4, 4))
        declared = "aadhaar_front" if kind == "eaadhaar_front" else "aadhaar_back"
    else:
        number = make_pan(rng, p.father)
        img, _ = render_pan_card(p, number, rng) if kind == "pan_card" else render_epan_printout(p, number, rng)
        spec = CaptureSpec() if kind == "pan_card" else CaptureSpec(card_width=rng.uniform(1450, 1550),
                                                                   rotation_deg=rng.uniform(-3, 3))
        declared = "pan"
    fname = f"real_{i + 1:03d}_{kind}.jpg"
    (OUT / fname).write_bytes(capture(img, spec, "B", rng))
    return {"file": fname, "kind": kind, "declared_type": declared, "number": number, "dob": p.dob.isoformat()}


def _check(lab: dict) -> dict:
    from app.core.security import aadhaar_hmac
    from app.validation.api import validate_image

    out = validate_image((OUT / lab["file"]).read_bytes(), lab["declared_type"])
    r = out.result
    f = r.fields or {}
    if lab["declared_type"].startswith("aadhaar"):
        number_ok = out.aadhaar_hmac is not None and out.aadhaar_hmac == aadhaar_hmac(lab["number"])
    else:
        number_ok = f.get("id_number_display") == lab["number"]
    return {"file": lab["file"], "kind": lab["kind"], "status": r.status, "codes": [i.code for i in r.issues],
            "number_ok": number_ok, "dob_ok": f.get("dob") == lab["dob"] if "dob" in f else None,
            "ms": r.timings_ms.total}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=40)
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    with ProcessPoolExecutor(max_workers=3) as ex:
        labels = list(ex.map(_make, range(a.n)))
        (OUT / "labels.jsonl").write_text("\n".join(json.dumps(x) for x in labels) + "\n", encoding="utf-8")
        res = list(ex.map(_check, labels))
    summary = {}
    for kind in ("eaadhaar_front", "eaadhaar_back", "pan_card", "epan_printout"):
        rs = [r for r in res if r["kind"] == kind]
        dobs = [r["dob_ok"] for r in rs if r["dob_ok"] is not None]
        summary[kind] = {"n": len(rs), "accepted": sum(r["status"] == "accepted" for r in rs),
                         "number_correct": sum(r["number_ok"] for r in rs),
                         "dob_correct": f"{sum(dobs)}/{len(dobs)}" if dobs else "n/a",
                         "false_invalid": sum(r["status"] == "invalid" for r in rs),
                         "retake_codes": sorted({c for r in rs if r["status"] == "fixable" for c in r["codes"]}),
                         "median_ms": sorted(r["ms"] for r in rs)[len(rs) // 2] if rs else 0}
    RESULT.write_text(json.dumps({"note": "Synthetic SPECIMEN documents in the real current layouts; not used for "
                                          "tuning. Real-world accuracy still needs a pilot.",
                                  "summary": summary, "items": res}, indent=1), encoding="utf-8")
    for k, v in summary.items():
        print(f"{k:16} {v}")
    print(f"wrote {RESULT}")


if __name__ == "__main__":
    main()
