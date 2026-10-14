"""End-to-end engine check on the committed demo images (runs real OCR, ~15 s)."""
from pathlib import Path

import pytest

from app.validation.api import check_consistency, validate_image
from datagen.generate_demo import DEMO_DIR, EXPECT

IMAGES = sorted(DEMO_DIR.glob("*.jpg"))


@pytest.mark.skipif(not IMAGES, reason="demo images not generated")
@pytest.mark.parametrize("path", IMAGES, ids=lambda p: p.name[:2])
def test_demo_image_outcome(path: Path):
    declared, status, code = EXPECT[path.name[:2]]
    out = validate_image(path.read_bytes(), declared)
    r = out.result
    assert r.status == status, [i.code for i in r.issues]
    if code:
        assert code in [i.code for i in r.issues]
    if status == "fixable" and code in ("BLUR", "GLARE", "CROPPED"):
        assert r.fields is None and r.ocr is None  # quality first: no OCR on a bad capture
        assert r.timings_ms.total < 1000
    if r.fields and declared.startswith("aadhaar"):
        assert r.fields["id_number_display"].startswith("XXXX XXXX ")


def _extracted(name, declared):
    return validate_image((DEMO_DIR / name).read_bytes(), declared).extracted


@pytest.mark.skipif(not IMAGES, reason="demo images not generated")
def test_demo_consistency_story():
    front = _extracted("02_aadhaar_front_clean.jpg", "aadhaar_front")
    back = _extracted("03_aadhaar_back_clean.jpg", "aadhaar_back")
    pan = _extracted("05_pan_clean_initials.jpg", "pan")
    other = _extracted("09_pan_other_person.jpg", "pan")
    likely = check_consistency([front, back, pan])
    assert likely.name_tier == "likely_match"
    assert any(i.evidence.get("initial_expanded") == "R→RAJENDRAN" for i in likely.issues)
    assert check_consistency([front, back, other]).name_tier == "mismatch"
