"""Error injectors. Each mutates a CaptureSpec / sample and returns the true codes it causes."""
import random

from datagen.capture import CaptureSpec

DOC_TYPES = ["aadhaar_front", "aadhaar_back", "pan", "voter_id"]


def inj_blur(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    if rng.random() < 0.6:
        spec.blur_sigma = rng.uniform(2.5, 5.0)
    else:
        spec.motion_len = rng.randint(12, 25)
    return ["BLUR"]


def inj_mild_blur(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.blur_sigma = rng.uniform(0.8, 1.3)
    return []  # should pass: keeps the blur detector honest


def inj_glare(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.glare_frac = rng.uniform(0.04, 0.12)
    return ["GLARE"]


def inj_dark(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.gain = rng.uniform(0.28, 0.45)  # under-exposed
    spec.gamma = rng.uniform(1.2, 1.6)
    return ["TOO_DARK"]


def inj_bright(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.gamma = rng.uniform(0.3, 0.45)
    spec.washout = rng.uniform(0.15, 0.35)
    return ["TOO_BRIGHT"]


def inj_crop(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.crop_frac = rng.uniform(0.12, 0.30)
    spec.crop_side = rng.choice(["left", "right", "top", "bottom"])
    return ["CROPPED"]


def inj_lowres(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    spec.downscale_to_card_w = rng.uniform(300, 550)
    return ["LOW_RESOLUTION"]


def inj_wrong_type(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    s["declared_type"] = rng.choice([t for t in DOC_TYPES if t != s["doc_type"]])
    return ["WRONG_DOC_TYPE"]


def inj_invalid_checksum(spec: CaptureSpec, s: dict, rng: random.Random) -> list[str]:
    if s["doc_type"] not in ("aadhaar_front", "aadhaar_back"):
        s["doc_type"] = s["declared_type"] = rng.choice(["aadhaar_front", "aadhaar_back"])
    s["number_valid"] = False
    return ["INVALID_CHECKSUM"]


INJECTORS = {
    "blur": inj_blur, "mild_blur": inj_mild_blur, "glare": inj_glare, "dark": inj_dark, "bright": inj_bright,
    "crop": inj_crop, "lowres": inj_lowres, "wrong_type": inj_wrong_type, "invalid_checksum": inj_invalid_checksum,
}

# Pairs that can co-occur in one photo (5% of images carry two errors).
COMPATIBLE_PAIRS = [("blur", "dark"), ("glare", "crop"), ("blur", "glare"), ("dark", "crop"), ("bright", "crop"),
                    ("lowres", "glare"), ("blur", "crop")]
