"""Labelled synthetic phone captures.

    python -m datagen.generate --split tune|test --n 300 [--seed N] [--workers 6]

Writes datagen/out/{split}/img_00001.jpg and labels.jsonl. tune uses background set A, test set B.
"""
import argparse
import json
import random
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from datagen.capture import CaptureSpec, capture
from datagen.errors import COMPATIBLE_PAIRS, DOC_TYPES, INJECTORS
from datagen.identities import Person, make_person
from datagen.numbers import make_aadhaar, make_epic, make_invalid_aadhaar, make_pan
from datagen.templates import render

OUT = Path(__file__).with_name("out")
SPLIT_BG = {"tune": "A", "test": "B"}
SPLIT_SEED = {"tune": 1001, "test": 2002}
SINGLE = [k for k in INJECTORS if k != "mild_blur"]


def pick_errors(rng: random.Random) -> list[str]:
    r = rng.random()
    if r < 0.30:
        return []
    if r < 0.38:
        return ["mild_blur"]
    if r < 0.43:
        return list(rng.choice(COMPATIBLE_PAIRS))
    return [rng.choice(SINGLE)]


def card_number(doc_type: str, p: Person, valid: bool, rng: random.Random) -> str:
    if doc_type in ("aadhaar_front", "aadhaar_back"):
        return make_aadhaar(rng) if valid else make_invalid_aadhaar(rng)
    if doc_type == "pan":
        return make_pan(rng, p.father)
    return make_epic(rng)


def card_name(doc_type: str, p: Person, rng: random.Random) -> str | None:
    if doc_type == "aadhaar_back":
        return None
    if doc_type == "pan":
        return p.full
    if doc_type == "voter_id":
        return rng.choice([p.initial_last, p.full])
    return rng.choice([p.initial_first, p.initial_last, p.full])


def truth_for(doc_type: str, p: Person, number: str, name: str | None) -> dict:
    return {"id_number": number, "name": name,
            "dob": None if doc_type == "aadhaar_back" else p.dob.isoformat(),
            "gender": p.gender if doc_type in ("aadhaar_front", "voter_id") else None,
            "father_name": p.father if doc_type in ("pan", "voter_id") else None,
            "pin_code": p.pin if doc_type == "aadhaar_back" else None}


def make_sample(split: str, seed: int, i: int) -> dict:
    rng = random.Random(seed * 1_000_003 + i)
    doc_type = DOC_TYPES[i % 4] if rng.random() < 0.5 else rng.choice(DOC_TYPES)
    s = {"doc_type": doc_type, "declared_type": doc_type, "number_valid": True}
    spec = CaptureSpec()
    errors = pick_errors(rng)
    codes: list[str] = []
    for e in errors:
        codes += INJECTORS[e](spec, s, rng)
    p = make_person(rng)
    number = card_number(s["doc_type"], p, s["number_valid"], rng)
    name = card_name(s["doc_type"], p, rng)
    card = render(s["doc_type"], p, number, name, rng)
    jpeg = capture(card, spec, SPLIT_BG[split], rng)
    fname = f"img_{i + 1:05d}.jpg"
    (OUT / split / fname).write_bytes(jpeg)
    return {"file": fname, "doc_type": s["doc_type"], "declared_type": s["declared_type"],
            "true_codes": sorted(set(codes)), "injected": errors, "number_valid": s["number_valid"],
            "truth": truth_for(s["doc_type"], p, number, name), "bg_set": SPLIT_BG[split]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["tune", "test"], required=True)
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    seed = a.seed if a.seed is not None else SPLIT_SEED[a.split]
    out = OUT / a.split
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("img_*.jpg"):
        old.unlink()
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        labels = list(ex.map(make_sample, [a.split] * a.n, [seed] * a.n, range(a.n), chunksize=8))
    with open(out / "labels.jsonl", "w", encoding="utf-8") as f:
        for lab in labels:
            f.write(json.dumps(lab) + "\n")
    counts: dict[str, int] = {}
    for lab in labels:
        for c in lab["true_codes"] or ["(clean)"]:
            counts[c] = counts.get(c, 0) + 1
    print(f"{a.split}: {a.n} images, bg set {SPLIT_BG[a.split]} -> {out}")
    for c, n in sorted(counts.items()):
        print(f"  {c:18} {n}")


if __name__ == "__main__":
    main()
