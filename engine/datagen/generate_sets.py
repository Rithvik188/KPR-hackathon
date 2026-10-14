"""Citizen document sets for the consistency evaluation (all clean captures).

    python -m datagen.generate_sets --n 60

n/3 match, n/3 likely_match, n/3 mismatch, plus 8 sets missing aadhaar_back. Half go to tune
(background set A), half to test (set B). Writes datagen/out/sets/{tune,test}/set_xxx/*.jpg + sets.jsonl.
"""
import argparse
import json
import random
import shutil
from datetime import timedelta

from datagen.capture import CaptureSpec, capture
from datagen.generate import OUT, truth_for
from datagen.identities import FATHERS, GIVEN_F, GIVEN_M, Person, make_person, random_dob
from datagen.numbers import make_aadhaar, make_epic, make_pan
from datagen.templates import render

SETS_OUT = OUT / "sets"


def _other_person(p: Person, rng: random.Random) -> tuple[Person, str]:
    """A different citizen who would be confused with p."""
    same_initial = [f for f in FATHERS if f[0] == p.father[0] and f != p.father]
    if same_initial and rng.random() < 0.6:
        # Same given name and initial, different father (Rajendran vs Ramesh) and a different DOB.
        dob = p.dob + timedelta(days=rng.choice([-1, 1]) * rng.randint(40, 4000))
        return Person(p.given, rng.choice(same_initial), p.gender, dob, p.house, p.street, p.place, p.pin), "father"
    pool = [g for g in (GIVEN_M if p.gender == "M" else GIVEN_F) if g != p.given]
    dob = p.dob if rng.random() < 0.5 else random_dob(rng)
    return Person(rng.choice(pool), p.father, p.gender, dob, p.house, p.street, p.place, p.pin), "given"


def make_set(kind: str, idx: int, split: str, seed: int, missing_back: bool) -> dict:
    rng = random.Random(seed * 7919 + idx)
    p = make_person(rng)
    second = rng.choice(["pan", "voter_id"])
    aadhaar = make_aadhaar(rng)
    holder2, variant = p, None
    if kind == "match":
        a_name = p.full if second == "pan" else rng.choice([p.full, p.initial_last])
        n2 = a_name
    elif kind == "likely_match":
        a_name = p.initial_first
        n2 = p.full
    else:
        holder2, variant = _other_person(p, rng)
        a_name = p.initial_first if variant == "father" else p.full
        n2 = holder2.full
    docs = [("aadhaar_front", p, aadhaar, a_name)]
    if not missing_back:
        docs.append(("aadhaar_back", p, aadhaar, None))
    num2 = make_pan(rng, holder2.father) if second == "pan" else make_epic(rng)
    docs.append((second, holder2, num2, n2))

    name = f"set_{idx:03d}"
    d = SETS_OUT / split / name
    d.mkdir(parents=True, exist_ok=True)
    files = {}
    for doc_type, person, number, nm in docs:
        card = render(doc_type, person, number, nm, rng)
        (d / f"{doc_type}.jpg").write_bytes(capture(card, CaptureSpec(), "A" if split == "tune" else "B", rng))
        files[doc_type] = {"file": f"{name}/{doc_type}.jpg", "truth": truth_for(doc_type, person, number, nm)}
    return {"set": name, "expected_tier": kind, "mismatch_variant": variant,
            "dob_match": holder2.dob == p.dob, "back_missing": missing_back, "docs": files}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--extra-missing-back", type=int, default=8)
    ap.add_argument("--seed", type=int, default=3003)
    a = ap.parse_args()
    if SETS_OUT.exists():
        shutil.rmtree(SETS_OUT)
    kinds = ["match", "likely_match", "mismatch"]
    jobs = [(kinds[i % 3], False) for i in range(a.n)] + [(kinds[i % 3], True) for i in range(a.extra_missing_back)]
    rows = {"tune": [], "test": []}
    for i, (kind, missing) in enumerate(jobs):
        split = "tune" if i % 2 == 0 else "test"
        rows[split].append(make_set(kind, i, split, a.seed, missing))
    for split, rs in rows.items():
        with open(SETS_OUT / split / "sets.jsonl", "w", encoding="utf-8") as f:
            for r in rs:
                f.write(json.dumps(r) + "\n")
        print(f"{split}: {len(rs)} sets ({sum(r['back_missing'] for r in rs)} missing back)")


if __name__ == "__main__":
    main()
