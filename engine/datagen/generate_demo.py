"""Deterministic demo images for the live demo (demo/images/). All SPECIMEN, all synthetic.

    python -m datagen.generate_demo [--seed 43] [--search 10]   (--search re-verifies with the real engine)

The citizen in 02/03/05 is the same person: Aadhaar shows "R. KARTHIK", PAN shows "KARTHIK RAJENDRAN".
09 is a different person with the same given name and initial (KARTHIK RAMESH) and a different DOB.
"""
import argparse
import random
from datetime import date
from pathlib import Path

from datagen.capture import CaptureSpec, capture
from datagen.identities import Person
from datagen.numbers import make_aadhaar, make_epic, make_invalid_aadhaar, make_pan
from datagen.templates import render

DEMO_DIR = Path(__file__).resolve().parents[2] / "demo" / "images"


def build(seed: int) -> dict[str, bytes]:
    rng = random.Random(seed)
    karthik = Person("KARTHIK", "RAJENDRAN", "M", date(1998, 4, 12), "27", "GANDHI STREET", "SULUR", "641402")
    other = Person("KARTHIK", "RAMESH", "M", date(1995, 9, 3), "9", "NEHRU NAGAR", "PEELAMEDU", "641004")
    meena = Person("MEENA", "SUBRAMANIAN", "F", date(1990, 11, 3), "14", "TEMPLE STREET", "POLLACHI", "642001")
    aadhaar = make_aadhaar(rng)
    pan = make_pan(rng, karthik.father)
    epic = make_epic(rng)

    def shot(doc, person, number, name, **spec) -> bytes:
        s = CaptureSpec(card_width=spec.pop("card_width", 1250), rotation_deg=spec.pop("rotation_deg", 4.0),
                        noise_sigma=spec.pop("noise_sigma", 3.0), jpeg_quality=spec.pop("jpeg_quality", 88), **spec)
        return capture(render(doc, person, number, name, rng), s, "B", rng)

    return {
        "01_aadhaar_front_blurry.jpg": shot("aadhaar_front", karthik, aadhaar, karthik.initial_first, blur_sigma=4.2),
        "02_aadhaar_front_clean.jpg": shot("aadhaar_front", karthik, aadhaar, karthik.initial_first),
        "03_aadhaar_back_clean.jpg": shot("aadhaar_back", karthik, aadhaar, None, rotation_deg=-3.0),
        "04_pan_glare.jpg": shot("pan", karthik, pan, karthik.full, glare_frac=0.08),
        "05_pan_clean_initials.jpg": shot("pan", karthik, pan, karthik.full, rotation_deg=-2.5),
        "06_voter_cropped.jpg": shot("voter_id", karthik, epic, karthik.initial_last, crop_frac=0.22,
                                     crop_side="right"),
        "07_voter_clean.jpg": shot("voter_id", karthik, epic, karthik.initial_last, rotation_deg=3.0),
        "08_aadhaar_invalid_number.jpg": shot("aadhaar_front", meena, make_invalid_aadhaar(rng), meena.initial_first),
        "09_pan_other_person.jpg": shot("pan", other, make_pan(rng, other.father), other.full),
    }


# file prefix -> (declared_type, expected status, code that must be present)
EXPECT = {"01": ("aadhaar_front", "fixable", "BLUR"), "02": ("aadhaar_front", "accepted", None),
          "03": ("aadhaar_back", "accepted", None), "04": ("pan", "fixable", "GLARE"),
          "05": ("pan", "accepted", None), "06": ("voter_id", "fixable", "CROPPED"),
          "07": ("voter_id", "accepted", None), "08": ("aadhaar_front", "invalid", "INVALID_CHECKSUM"),
          "09": ("pan", "accepted", None)}


def verify(images: dict[str, bytes]) -> list[str]:
    """Run the real engine on each demo image; return the failures."""
    from app.validation.api import validate_image

    fails = []
    for name, data in images.items():
        declared, status, code = EXPECT[name[:2]]
        r = validate_image(data, declared).result
        codes = [i.code for i in r.issues]
        if r.status != status or (code and code not in codes):
            fails.append(f"{name}: got {r.status} {codes}, want {status} {code or ''}")
    return fails


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=43)
    ap.add_argument("--verify", action="store_true", help="check every image gives its intended result")
    ap.add_argument("--search", type=int, default=0, help="try this many seeds until all checks pass")
    a = ap.parse_args()
    seed, images = a.seed, build(a.seed)
    if a.verify or a.search:
        for seed in range(a.seed, a.seed + max(1, a.search)):
            images = build(seed)
            fails = verify(images)
            print(f"seed {seed}: {'OK' if not fails else fails}")
            if not fails:
                break
        else:
            raise SystemExit("no seed passed all demo checks")
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in images.items():
        (DEMO_DIR / name).write_bytes(data)
    print(f"wrote {len(images)} demo images (seed {seed}) to {DEMO_DIR}")


if __name__ == "__main__":
    main()
