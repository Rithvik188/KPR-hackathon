# Person 1: Engine Plan

**You own:**
- `engine/app/main.py`, `engine/app/core/`, `engine/app/validation/`, `engine/app/routers/`
- `engine/datagen/`, `engine/evaluation/`, `engine/tests/` (except `tests/ops/`)
- `scripts/`, `contract/`, `demo/images/`

**Your job:** make the validation pipeline real, fast and honestly measured. Person 2 builds everything users see, and depends on your contract and your Python functions (`contract/api.md` section 4).

**How to use this file with Claude Code:** start each session with:
> Read CLAUDE.md, contract/api.md and plans/PERSON1_ENGINE.md. We are starting step **P1-X**. Use plan mode, then implement. Stay inside my owned paths. Commit when the "Done when" checks pass.

Time stamps are hours from the start. Sync points are fixed. Be ready for them even if a step is unfinished: commit what works, stub the rest.

---

## Pre-event (do this the day before)

1. Install Python 3.11, Node 20, Git and ngrok, and sign up for an ngrok account.
2. Create a scratch venv and run `pip install fastapi uvicorn[standard] sqlmodel python-multipart opencv-python-headless numpy pillow easyocr rapidfuzz imagehash cryptography albumentations pytest reportlab`.
3. **Download the OCR models:** run `python -c "import easyocr; easyocr.Reader(['en'], gpu=False)"` once. The models download to `~/.EasyOCR/`.
4. **Benchmark OCR:**
   - Render a 1000×630 image with some text using Pillow.
   - Time `reader.readtext()` 5 times.
   - If the average is over 3 s, install `rapidocr_onnxruntime`, benchmark that, and use whichever is faster. Write the result down.
5. Check the hackathon rules on pre-written code. This kit contains only plans and specs, which is normally fine, but confirm.

---

## P1-0 · Kickoff, together with Person 2 (0:00–0:30)

Follow `plans/INTEGRATION.md` §2. You create the repo and push the kit. Then read `contract/api.md` together and agree on it. After this point you are the contract owner.

---

## P1-1 · Backend skeleton and stubs (0:30–1:30) → **Sync 1**

**Goal:** a running FastAPI app that matches the contract, with stub validation, so Person 2 can integrate immediately.

**Build:**
- **Project setup:**
  - `engine/requirements.txt` with pinned versions from your pre-event install.
  - `.env.example` at the repo root containing `AADHAAR_HMAC_SECRET`, `IMAGE_ENC_KEY`, `DATABASE_URL=sqlite:///./data/sevaicheck.db`, `DATA_DIR=./data`, `OCR_ENGINE=easyocr`, `SERVE_WEB=0`.
  - `.gitignore` covering `.env`, `engine/data/`, `engine/datagen/out/`, `node_modules/`, `web/dist/`, `__pycache__/` and `.venv/`.
- **`app/core/config.py`:** pydantic-settings that read `.env`. Fail loudly if the secrets are missing.
- **`app/core/db.py`:** SQLModel engine, `create_db()` and a `get_session` dependency.
- **`app/core/models.py`:** every table from contract §5. **Push this by about 0:45** and tell Person 2.
- **`app/core/storage.py`:** `save_image`, `load_image` and `delete_image`, using Fernet with `IMAGE_ENC_KEY`. Files go to `DATA_DIR/images/{document_id}.bin`.
- **`app/core/security.py`:**
  - `aadhaar_hmac(digits)` using HMAC-SHA256.
  - `mask_aadhaar(digits)` returning `XXXX XXXX 1234`.
  - `mask_phone`.
- **`app/validation/types.py`:**
  - Pydantic models exactly matching the contract: `Issue`, `ValidationResult`, `ConsistencyResult`.
  - Dataclasses `ValidationOutcome` and `ExtractedDoc`.
- **`app/validation/messages.py`:**
  - Loads `contract/messages.json`.
  - `make_issue(code, evidence)` fills in severity, audience and messages from a code table that mirrors contract §1.
- **`app/validation/api.py` (STUBS):**
  - `validate_image` returns the `validate_accepted.json` shape, with `doc_type = declared_type or "aadhaar_front"`, `card_jpeg` = the input bytes and `aadhaar_hmac` = `None`.
  - `check_consistency` returns `not_enough_data`.
  - `find_duplicates` returns `[]`.
- **Routers (`app/routers/`):**
  - `health.py`
  - `validate.py`, which enforces 10 MB and JPG/PNG (returning `FILE_TOO_LARGE`/`UNSUPPORTED_FILE` as ValidationResults, not HTTP errors)
  - `metrics_detection.py`, which exposes `load_detection_metrics() -> dict`. It reads `engine/evaluation/results.json`, or falls back to `contract/fixtures/metrics_detection.json`. Person 2 imports this function.
- **`app/main.py`:**
  - Mounts all routers under `/api`. Registers an error handler producing `{"error": {...}}`. Calls `create_db()` on startup.
  - **Ops hook** (so you never edit Person 2's folder):
    ```python
    try:
        from app.ops import router as ops_router, startup as ops_startup
        app.include_router(ops_router, prefix="/api")
    except ImportError:
        ops_router, ops_startup = None, None
    # in lifespan/startup: if ops_startup: await ops_startup()
    ```
  - If `SERVE_WEB=1`: mount `../web/dist` at `/`, with an SPA fallback to `index.html` for non-`/api` paths.
  - CORS allowing `http://localhost:5173`, as a safety net alongside the proxy.
- **`scripts/dev.sh`:** starts `uvicorn app.main:app --reload --port 8000` (from `engine/`) and `npm run dev` (from `web/`). Ctrl-C kills both.
- **`scripts/contract_check.py`:**
  - Calls every GET endpoint, plus `POST /api/validate` with a tiny generated JPEG.
  - Recursively compares the response key sets against the matching fixture.
  - Prints PASS/FAIL per endpoint. Skips endpoints returning 404 with a "not yet implemented" note.

**Done when:**
- `curl localhost:8000/api/health` returns ok.
- `curl -F file=@any.jpg -F declared_type=pan localhost:8000/api/validate` returns contract-shaped JSON.
- `contract_check.py` passes for P1 endpoints.
- `/openapi.json` loads.

---

## P1-2 · Synthetic data generator (1:30–2:20)

**Goal:** a labelled dataset of realistic "phone captures" of SPECIMEN cards, with separate tune and test splits.

**Build** in `engine/datagen/`:
- **`identities.py`:** fake citizens.
  - Tamil Nadu naming styles: `R. KARTHIK`, `KARTHIK R`, `KARTHIK RAJENDRAN` (the father's name is the initial).
  - A pool of about 60 given names and 60 father names, all common names, no public figures.
  - DOB between 1950 and 2006, gender, and a fake Coimbatore-area address with a PIN in `641xxx` or `642xxx`.
- **`numbers.py`:**
  - Verhoeff `generate`/`validate`. Aadhaar numbers are 12 digits, the first digit is 2–9, and the last digit is the Verhoeff check digit.
  - `make_invalid_aadhaar()` with a wrong check digit.
  - PAN `[A-Z]{3}P[A-Z][0-9]{4}[A-Z]`. The 5th character is the first letter of the father's name/surname.
  - EPIC `[A-Z]{3}[0-9]{7}`.
- **`templates.py`:** render cards at **1012×638 px**, the ID-1 card ratio, with Pillow and DejaVu Sans.
  - **Text-only header strings, no emblems or logos:**
    - `aadhaar_front`: "GOVERNMENT OF INDIA", a photo placeholder box, name, "DOB: dd/mm/yyyy", "MALE/FEMALE", and the number as `1234 5678 9012`.
    - `aadhaar_back`: "UNIQUE IDENTIFICATION AUTHORITY OF INDIA", "Address:", the address lines with PIN, and the number.
    - `pan`: "INCOME TAX DEPARTMENT", "Permanent Account Number Card", the PAN, name, father's name and DOB.
    - `voter_id`: "ELECTION COMMISSION OF INDIA", "ELECTOR PHOTO IDENTITY CARD", the EPIC, name, father's name and DOB.
  - A diagonal semi-transparent watermark reading `SPECIMEN — NOT A REAL DOCUMENT`.
  - Slight per-card variation: font size ±8%, position jitter ±6 px, background tint.
- **`capture.py`:** simulates a phone photo. Every image gets:
  - Composited onto a background on a 1600×1200 canvas. Card width is 900–1500 px.
  - Random perspective (corner jitter up to 5%) and rotation ±10°.
  - A lighting gradient, sometimes a soft shadow, Gaussian noise σ 2–6, and JPEG quality 65–92.
  - **Backgrounds are procedural (wood, fabric, desk grey, paper). Background set A is used for `tune`, set B for `test`,** so thresholds can't overfit the backgrounds.
- **`errors.py`:** each injector returns `(image, true_codes)`.

  | Injector | What it does | True code |
  |---|---|---|
  | blur | Gaussian σ 2.5–5 or motion blur 12–25 px | `BLUR` |
  | mild blur | σ 0.8–1.3 | none (should pass; this keeps the test honest) |
  | glare | Elliptical white-hot blob covering 4–12% of the card, placed over the text area | `GLARE` |
  | dark | Gamma 2.2–3.0 | `TOO_DARK` |
  | bright | Gamma 0.3–0.45 plus washout | `TOO_BRIGHT` |
  | crop | Shift the card so 12–30% of it leaves the frame on one side | `CROPPED` |
  | lowres | Card width 300–550 px | `LOW_RESOLUTION` |
  | wrong type | Render type X but set `declared_type` to type Y | `WRONG_DOC_TYPE` |
  | invalid checksum | Clean image with an invalid Aadhaar number | `INVALID_CHECKSUM` |
  | clean | No injected error | none |

- **`generate.py`** (`python -m datagen.generate --split tune|test --n 300 --seed N`):
  - Mix: clean 30%, mild blur 8%, then the remaining injectors about 7% each, with 5% of images carrying two errors.
  - Doc types are roughly equal across `aadhaar_front`, `aadhaar_back`, `pan` and `voter_id`.
  - Writes `datagen/out/{split}/img_00001.jpg` and `datagen/out/{split}/labels.jsonl`. Each label line is: `{"file", "doc_type", "declared_type", "true_codes", "number_valid", "truth": {"id_number", "name", "dob", "gender"}, "bg_set"}`.
- **`generate_sets.py`** (`--n 60`): produces citizen document sets for the consistency evaluation. Each set has `aadhaar_front` + `aadhaar_back` + `pan` or `voter_id`, all clean captures.
  - **20 `match`:** the same name string on both cards.
  - **20 `likely_match`:** the Aadhaar shows `R. KARTHIK` and the PAN shows `KARTHIK RAJENDRAN`.
  - **20 `mismatch`:** a different father's name with the same initial (Rajendran vs Ramesh) plus a different DOB, or a different given name.
  - **8 extra sets missing `aadhaar_back`.**
  - Half the sets go to tune and half to test. Writes `datagen/out/sets/{tune,test}/set_xxx/*.jpg` plus `sets.jsonl`.
- **`demo/images/`:** copy and rename the best examples:
  - `01_aadhaar_front_blurry.jpg`, `02_aadhaar_front_clean.jpg`, `03_aadhaar_back_clean.jpg`
  - `04_pan_glare.jpg`, `05_pan_clean_initials.jpg`, `06_voter_cropped.jpg`, `07_voter_clean.jpg`
  - `08_aadhaar_invalid_number.jpg`, `09_pan_other_person.jpg`
  - The citizen in 02/03/05 is the same "R. KARTHIK / KARTHIK RAJENDRAN" person.

**Done when:**
- Both splits and the sets exist.
- You've looked at 20 random images, and they look like phone photos of cards, not clean renders.

---

## P1-3 · Quality checks (2:20–3:05)

**Goal:** a fast, deterministic quality gate that runs in under 300 ms.

**Build** `app/validation/quality.py`, reading all thresholds from `app/validation/thresholds.json`:
1. **File checks:** decode with OpenCV. On failure, return `UNSUPPORTED_FILE`.
2. **Card detection:**
   - Resize to a 1200 px long side.
   - Grayscale → bilateral filter → Canny → dilate → `findContours`.
   - Take the largest 4-point `approxPolyDP` contour with an area over `card_min_area_frac` (0.12).
   - If none is found, try a `minAreaRect` fallback on the largest contour.
   - If still nothing, return `CARD_NOT_FOUND`.
3. **CROPPED:**
   - Any corner within `crop_border_px` (6) of the image edge, or
   - the contour area divided by the image area exceeds 0.97, or
   - the detected quad's aspect ratio is more than 20% away from 1.585.
4. **Perspective correction:** warp to 1000×630. If the measured rotation is over 2°, add `SKEW_CORRECTED` (info).
5. **LOW_RESOLUTION:** the card's width in the *original* image is below `min_card_width_px` (650).
6. **BLUR:** variance of the Laplacian on the warped grayscale card is below `blur_min` (start at 100).
7. **GLARE:**
   - In HSV on the warped card, take pixels with V > `glare_v` (245) and S < `glare_s` (40).
   - Find the largest connected blob.
   - Flag if the blob covers more than `glare_blob_frac` (0.015) of the card.
8. **TOO_DARK / TOO_BRIGHT:** the mean of the gray card is below `dark_max` (60) or above `bright_min` (205).
9. **Return** a `quality` dict (all measured values plus `passed`), the issues (each with `evidence` = value + threshold) and the warped card image.

**Starting `thresholds.json`:**
```json
{"card_min_area_frac": 0.12, "crop_border_px": 6, "min_card_width_px": 650, "blur_min": 100,
 "glare_v": 245, "glare_s": 40, "glare_blob_frac": 0.015, "dark_max": 60, "bright_min": 205,
 "ocr_min_confidence_for_rules": 0.85, "classify_min_score": 2, "phash_max_distance": 6,
 "name_match_min": 92, "name_likely_min": 80}
```

**Wire it into `validate_image`:** run quality, and **if there is any blocking issue, return immediately** with `fields=null`, `ocr=null` and timings filled in.

**Done when:**
- `/api/validate` on `demo/images/01_*` returns `BLUR` in under 1 s.
- `02_*` passes quality.
- A quick script prints the detected codes vs the true codes for 50 tune images, and they look mostly right.

---

## P1-4 · OCR, classification, extraction, rules (3:05–4:00) → **Sync 2**

**Build:**
- **`ocr.py`:**
  - A singleton reader created at startup and warmed up on a blank image.
  - `read(card_bgr) -> list[(text, conf, bbox)]` on the 1000×630 warped card.
  - The engine is selected by `OCR_ENGINE`.
- **`classify.py`:**
  - Keyword scoring on uppercased OCR text:
    - `aadhaar_front`: "GOVERNMENT OF INDIA", "DOB", "MALE/FEMALE", a 4-4-4 digit pattern
    - `aadhaar_back`: "UNIQUE IDENTIFICATION", "ADDRESS", a 6-digit PIN, a 4-4-4 digit pattern
    - `pan`: "INCOME TAX", "PERMANENT ACCOUNT", the PAN regex
    - `voter_id`: "ELECTION COMMISSION", "ELECTOR", the EPIC regex
  - Use fuzzy keyword matching (rapidfuzz `partial_ratio` ≥ 85).
  - If the top score is below `classify_min_score`, return `UNKNOWN_DOC_TYPE`.
  - If `declared_type` is set and differs from the detected type, return `WRONG_DOC_TYPE`.
- **`extract.py`:** per-type field extraction using regex plus positional heuristics (e.g. the name is the line just above "DOB" or after "Name"). Normalise DOB to ISO format. It returns the fields and the **confidence of the ID-number tokens**.
- **`rules.py`:**
  - **Confusable correction in number fields only.** In digit positions, map O/D→0, I/L/|→1, Z→2, S→5, B→8, G→6. For PAN, letter positions get the reverse map.
    - If a substitution was made and the corrected value passes its rule, add `OCR_AUTOCORRECTED` (info).
  - **The gate:** only run checksum and format rules if `quality.passed` and `id_number_confidence ≥ ocr_min_confidence_for_rules`. **Otherwise return `UNREADABLE`.**
  - **Aadhaar:** 12 digits, first digit 2–9, Verhoeff valid. Failure is `INVALID_CHECKSUM` (or `INVALID_FORMAT` for the wrong length or first digit).
  - **PAN:** `^[A-Z]{5}[0-9]{4}[A-Z]$` with the 4th character in `PCHFATBLJG`. Failure is `INVALID_FORMAT`.
  - **EPIC:** `^[A-Z]{3}[0-9]{7}$`. Failure is `INVALID_FORMAT`.
  - If the ID number can't be found at all, return `UNREADABLE`.
- **`validate_image`:** quality → (early return) → OCR → classify → extract → rules.
  - Compute `aadhaar_hmac` and `phash` (`imagehash.phash` of the warped card).
  - Set `card_jpeg` to the warped card, mask `id_number_display` and compute `status` with the contract rule.
- **Tests (`engine/tests/`):**
  - Verhoeff: generated numbers validate; every single-digit change fails; every adjacent transposition fails.
  - The PAN and EPIC regexes.
  - Confusable correction.
  - **The gate test:** a low-confidence invalid number returns `UNREADABLE`, never `INVALID_CHECKSUM`.
  - Masking never leaks more than 4 digits.
- **`scripts/smoke_test.py`:**
  - Creates an application via the API and uploads demo images 01→02→03→05.
  - Asserts the statuses: fixable, accepted, accepted, and `ready_for_officer` at the end.
  - It uses Person 2's endpoints, so expect it to fully pass only after Sync 2.

**Done when:**
- `pytest` passes.
- Demo images 02, 03, 05 and 07 are accepted with correct fields. 08 is `invalid`. 01 is `fixable/BLUR`.
- A full validation takes under 3 s on your laptop.
- Then go to **Sync 2** (INTEGRATION.md §4).

---

## P1-5 · Consistency and duplicates (4:00–5:15)

**Build** `consistency.py`:
- **`normalize_name`:** uppercase, strip punctuation and the "S/O"/"D/O" prefixes, then split into tokens. Single letters are initials.
- **Tier logic** (thresholds from `thresholds.json`):
  1. Compare full tokens with rapidfuzz `token_sort_ratio`. A score of at least `name_match_min` with no initials involved is `match`.
  2. **Initial expansion:** if name A has initial X and name B has a full token starting with X that isn't in A's tokens, drop that pair from both and compare the remaining tokens. If the remaining tokens match at ≥ `name_match_min`, it's a **candidate `likely_match`**. Record `initial_expanded: "R→RAJENDRAN"` in the evidence.
  3. A score between `name_likely_min` and `name_match_min` is also a candidate `likely_match`.
  4. **DOB is the tie-breaker.** A candidate `likely_match` stays `likely_match` only if the DOBs match. If the DOBs differ, it becomes `mismatch`.
  5. Everything else is `mismatch`.
- **DOB:** if any two documents have different DOBs, add `DOB_MISMATCH`.
- **`AADHAAR_BACK_MISSING`:** `aadhaar_front` is present and `aadhaar_back` is absent.
- **Issues:** `NAME_LIKELY_MATCH` (warning, officer) or `NAME_MISMATCH` (blocking).
- **`not_enough_data`:** fewer than two documents have a name.

**Then:**
- **`find_duplicates`** in `duplicates.py`: an exact HMAC match on `Document.aadhaar_hmac`, or a phash Hamming distance ≤ `phash_max_distance`, excluding the current application.
- **Tests:**
  - `R. KARTHIK` vs `KARTHIK RAJENDRAN` with the same DOB → `likely_match`.
  - vs `KARTHIK RAMESH` with a different DOB → `mismatch`.
  - Identical names → `match`.
  - Back missing → issue present.

**Done when:** tests pass and the consistency confusion matrix on the `tune` sets looks sensible (print it).

---

## P1-6 · Threshold tuning (5:15–6:30) → **Sync 3**

**Build** `evaluation/tune.py`:
- **Grid search per quality threshold, on the `tune` split only.** For each check:
  - Maximise F1 for its code.
  - **Subject to a false-positive rate on clean and mild-blur images of at most 5%.** A genuine citizen being told to retake is a cost.
- **Search ranges:**
  - `blur_min` 40–250, step 10
  - `glare_blob_frac` 0.005–0.04
  - `dark_max` 40–90
  - `bright_min` 180–230
  - `min_card_width_px` 500–800
  - `crop_border_px` 2–15
- Then tune `ocr_min_confidence_for_rules` in 0.70–0.95, choosing the value that **minimises false invalids** while keeping recall on `INVALID_CHECKSUM` ≥ 0.9.
- Then tune the name thresholds on the tune sets.
- **Cache per-image measurements** (blur score etc.) once, so the grid search runs on numbers and doesn't re-run OCR.
- Writes `thresholds.json` and prints a tune-split summary. **This summary is not for slides.**
- **Performance pass:**
  - Make sure the OCR reader is reused.
  - Resize before OCR.
  - Run the `/validate` work in FastAPI's threadpool (a plain `def` endpoint).
  - Log `timings_ms`.

**Done when:** `thresholds.json` is committed. Then go to **Sync 3**.

---

## P1-7 · Held-out evaluation and metrics (6:30–7:40)

**Build** `evaluation/run.py`, using the `test` split and test sets only:
- **Per code:** precision, recall, F1 and support, for every code that appears in the labels.
- **`doc_type_accuracy`:** measured on images with no quality errors.
- **`field_accuracy`:** exact match after normalisation, for the Aadhaar number, PAN, EPIC, DOB and name. Count name matches at rapidfuzz ratio ≥ 95.
- **`false_invalid_rate`:** among images whose truth is `number_valid = true`, the share with status `invalid`. **Make this prominent.**
- **`latency_ms`:** p50 and p95 for the quality-only path and the full path.
- **Consistency confusion matrix** on the test sets.
- **Output:** writes `evaluation/results.json` with `"source": "evaluation"` (the contract shape). Also writes `evaluation/report.md`, a human-readable table plus the 10 worst failures with file names.
- **Look at the failures.** If one category is near 0 or near 1, sanity-check it: a perfect score usually means the test is too easy. Write that honestly in `report.md`.

**Privacy audit (15 min):**
- Grep the logs, the DB (`sqlite3 ... "select fields_json from document"`) and every API response from the smoke test for any 12-digit run.
- Fix any leak.

**Done when:**
- `/api/metrics/detection` returns `source: "evaluation"`.
- `report.md` exists.
- The privacy grep is clean.

---

## P1-8 · Stretch, only if ahead at 7:00: Tamil name read (≤ 1 h, hard stop at 8:00)

**Steps:**
1. Install libraqm and add Noto Sans Tamil.
2. Verify that Pillow renders Tamil conjuncts correctly. Check with Person 2's eyes.
3. Add the Tamil name to `aadhaar_front` templates.
4. Add an EasyOCR `['ta','en']` reader used only on the name region.
5. Expose `fields.name_ta` as an optional additive field. Follow the contract protocol.

If it isn't clean by 8:00, `git stash` it and move on.

---

## P1-9 · Feature freeze (8:00) and final phase (8:00–11:00)

Follow `plans/INTEGRATION.md` §5–§7. Your specific jobs:
- Bug fixes in your folders only.
- Write the README "Engine" and "Evaluation" sections:
  - The pipeline diagram (Mermaid).
  - The threshold-tuning method.
  - The results table copied from `results.json`.
  - Limitations: synthetic data, no real-capture validation yet, and the next step is a pilot.
- Run the clean-room test on Person 2's laptop.
- In the demo, you narrate the engine and answer technical questions.
- **Prepare answers to these questions:**
  - How did you avoid overfitting?
  - Why not a deep model?
  - What happens with a real Aadhaar?
  - How is the Aadhaar stored?
  - What's your false-invalid rate, and why does it matter?
