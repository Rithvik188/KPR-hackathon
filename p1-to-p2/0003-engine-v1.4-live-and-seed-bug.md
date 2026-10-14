# P1→P2 #0003
Prefix: MERGED + BUG
Needs reply: yes (item 2)

1. **MERGED:** engine side of contract v1.4 is on `main` at `aa89f12`.
   - `check_consistency(docs, form={"name": ..., "dob": ...})` returns `form_check` + `FORM_NAME_MISMATCH` /
     `FORM_NAME_VARIANT` / `FORM_DOB_MISMATCH`. "KARTHIK R" typed vs Aadhaar "R. KARTHIK" counts as a **match**.
   - `validate_image(bytes, "<supporting_type>")`: page sharpness/exposure/resolution checks (no card detection) →
     `accepted` + info `CONTENT_NOT_VERIFIED`, or `BLUR` etc., or `WRONG_DOC_TYPE` (e.g. an Aadhaar photo in the
     birth-certificate slot). `fields={"title": ...}`, `extracted=None`, `card_jpeg` = the page photo.
   - New demo images: `10_parent_community_certificate`, `11_birth_certificate`, `12_income_proof`,
     `13_birth_certificate_blurry` (→ BLUR), `14_address_proof`. All 14 demo images are verified by
     `tests/test_engine_demo.py` + `tests/test_v14.py`.
2. **BUG (yours), found when running the full pytest:** `tests/ops/test_seed_alerts.py` fails on clean `main` (2 tests),
   also without my changes. Since the date rolled over (now 2026-10-15), the seed fires a **5th alert:
   `REJECT_SPIKE` at `off_perur_to`**, and `by_office` top changes to Perur. The seed looks time- or
   date-dependent (random draws relative to now?). Please pin it so exactly the 4 stories fire on any day. Otherwise the
   demo shows a spurious Perur alert.
3. Pytest status on `main`: 93 pass, 2 fail (both from item 2).
