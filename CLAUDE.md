# SevaiCheck — Shared Rules for Claude Code

SevaiCheck validates citizen ID proofs (Aadhaar, PAN, Voter ID) **at the counter, in seconds**, before they enter a government office's queue. It also gives officers a clean queue and gives admins an analytics view of where and why errors happen across Coimbatore district.

Two people build this **simultaneously**. Read this file, `contract/api.md` and your own plan file before doing anything:
- Person 1 (Engine): `plans/PERSON1_ENGINE.md`
- Person 2 (Product): `plans/PERSON2_PRODUCT.md`
- Merging and final assembly: `plans/INTEGRATION.md`

## 1. Folder ownership (hard rule)

| Path | Owner | Notes |
|---|---|---|
| `contract/` | Person 1 edits, both read | Changes follow the protocol in section 4 |
| `engine/app/main.py`, `engine/app/core/` | Person 1 | Config, DB, models, storage, security |
| `engine/app/validation/` | Person 1 | Quality, OCR, classification, rules, consistency, duplicates |
| `engine/app/routers/` | Person 1 | `/health`, `/validate`, `/metrics/detection` |
| `engine/datagen/`, `engine/evaluation/` | Person 1 | Synthetic data and accuracy evaluation |
| `engine/tests/` (except `tests/ops/`) | Person 1 | |
| `engine/app/ops/` | Person 2 | Applications, documents, alerts, seed, notifications, issues, ops metrics, reports |
| `engine/tests/ops/` | Person 2 | |
| `web/` | Person 2 | Entire frontend |
| `scripts/` | Person 1 | Person 2 asks for changes |
| `demo/images/` | Person 1 | Curated demo images |
| `demo/demo_script.md`, `slides/` | Person 2 | |
| `README.md` | Both | Person 1 writes the "Engine" and "Evaluation" sections; Person 2 writes everything else |

**Claude Code must never create, edit or delete files outside the current person's owned paths.** If a change is needed elsewhere, stop and tell the human what to ask their teammate.

## 2. Tech stack (do not change without both agreeing)

- **Backend:** Python 3.11, FastAPI, Uvicorn, SQLModel on SQLite, Pydantic v2
- **Image and OCR:** opencv-python-headless, numpy, Pillow, EasyOCR (English only)
  - Fallback OCR: RapidOCR (ONNX), only if the EasyOCR benchmark is above 3 s per image
- **Matching and security:** rapidfuzz, imagehash, stdlib `hmac`, `cryptography` (Fernet)
- **Testing:** pytest
- **Data generation:** albumentations, Pillow
- **Frontend:** Vite, React 18, TypeScript, Tailwind CSS, react-router, Recharts, react-leaflet + Leaflet
- **API types:** `openapi-typescript`, generated from the backend's `/openapi.json`
- **Ports:** backend `8000`, frontend `5173`
  - The frontend calls `/api/...`, and the Vite dev proxy forwards it to `:8000`
  - In the final build, FastAPI serves `web/dist` at `/`, so a single ngrok tunnel covers everything

## 3. Non-negotiable design rules

1. **"Can't read" is never "invalid".**
   - Run checksum or format rules only if quality checks passed and the ID-number OCR confidence is at least `thresholds.json → ocr_min_confidence_for_rules`.
   - Otherwise return `UNREADABLE`, which makes the status `fixable`, never `invalid`.
2. **Quality first, OCR second.** If any blocking quality issue is found, return immediately without running OCR. The target is under 1 s for this path.
3. **Name matching has three tiers:** `match`, `likely_match` (an officer confirms) or `mismatch`.
   - Initial-based matches (R. Karthik ↔ Karthik Rajendran) are at most `likely_match`.
   - DOB is the tie-breaker.
4. **Aadhaar privacy:**
   - Never return, log or store the full Aadhaar number. Return `XXXX XXXX 1234` only.
   - Store `HMAC-SHA256(AADHAAR_HMAC_SECRET, digits)` for duplicate checks. Never use a plain hash: there are only 10¹² possible numbers, so a plain hash is brute-forceable.
5. **Images are stored encrypted** with Fernet (`IMAGE_ENC_KEY`) and deleted when an application is approved or rejected.
6. **Alerts are computed from data by rules.** Never hardcode alert text containing numbers; every number in an alert comes from a query.
7. **Every citizen-facing message is bilingual** (`msg_en`, `msg_ta`) and comes from `contract/messages.json`.
8. **No real ID images, ever.** All cards are synthetic, watermarked `SPECIMEN — NOT A REAL DOCUMENT`, with no government emblem and no UIDAI, Income Tax or ECI logos. Use plain placeholder shapes instead.
9. **Honest metrics.** Detection metrics come only from the held-out `test` split, never from `tune`. Fixture files contain placeholder numbers marked `"FIXTURE"`, and those must never appear in slides.

## 4. Contract change protocol

1. Only Person 1 edits `contract/`.
2. Every change does all of the following:
   - Updates `contract/api.md`
   - Updates the matching fixture in `contract/fixtures/`
   - Bumps the version line at the top of `api.md`
   - Is committed alone, with a message starting `CONTRACT:`
3. Person 1 messages Person 2 with the change in one line.
4. **Additive changes only after Sync 2** (new optional fields are fine). **No renames or removals after Sync 3.**

## 5. Git rules

- **Branches:** Person 1 works on `p1`, Person 2 on `p2`. `main` must always run.
- **Commits:** Small and frequent, with prefixes `engine:`, `ops:`, `web:`, `datagen:`, `eval:`, `CONTRACT:` or `docs:`.
- **Merging:** Only at sync points, following `plans/INTEGRATION.md`. Person 1 merges first, then Person 2.
- **Never commit:** `.env`, `engine/data/`, `engine/datagen/out/`, `node_modules/` or `web/dist/`.

## 6. Commands

```bash
# one-time
cp .env.example .env            # then fill secrets (see INTEGRATION.md)
cd engine && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
cd web && npm install

# daily
./scripts/dev.sh                                  # backend :8000 + frontend :5173
python -m app.ops.seed --reset                    # (in engine/) reset DB + seed offices + 30 days of ops data
python -m datagen.generate --split tune --n 300   # (in engine/)
python -m datagen.generate --split test --n 300
python -m datagen.generate_sets --n 60
python -m evaluation.tune                         # writes app/validation/thresholds.json from tune split
python -m evaluation.run                          # writes evaluation/results.json from test split
pytest                                            # (in engine/)
python scripts/contract_check.py                  # verifies live API shapes match fixtures
cd web && npm run gen:types                       # regenerates src/api/types.gen.ts from backend
./scripts/serve_prod.sh                           # build web, serve everything on :8000
```

## 7. Working style for Claude Code

- **Start every session** by reading this file, `contract/api.md` and the person's plan. Then say which step of the plan you are on.
- **Use plan mode** before any step larger than about 30 minutes.
- **Commit at the end of every plan step.**
- **Write or update tests** for every rule in `engine/app/validation/rules.py` and `consistency.py`.
- **If a step runs 50% over its time budget,** stop and tell the human what to cut. Do not silently expand scope.
- **Prefer simple, readable code** over clever code. This is a 11-hour build that must be demoed live.
