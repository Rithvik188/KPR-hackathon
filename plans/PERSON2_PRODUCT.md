# Person 2: Product Plan

**You own:**
- `web/` (the entire frontend)
- `engine/app/ops/` (the operations backend: applications, documents, alerts, seed data, notifications, issues, ops metrics, reports)
- `engine/tests/ops/`
- `demo/demo_script.md`, `slides/`
- Most of `README.md`

**Your job:** everything a citizen, operator, officer or admin sees, plus the operational data and rules behind it. You call Person 1's validation through the Python functions in `contract/api.md` §4. Never reimplement validation logic yourself.

**How to use this file with Claude Code:** start each session with:
> Read CLAUDE.md, contract/api.md and plans/PERSON2_PRODUCT.md. We are starting step **P2-X**. Use plan mode, then implement. Stay inside my owned paths. Commit when the "Done when" checks pass.

**Model use:** use Opus for planning, the alert engine, the seed generator and debugging. Use Sonnet for routine UI components and styling. This saves your usage limit for later.

---

## Pre-event (the day before)

1. Install Node 20 and Python 3.11.
2. In a scratch folder, check that `npm create vite@latest` works.
3. Test-install `react-leaflet leaflet recharts react-router-dom` and `openapi-typescript`.
4. Make sure you can open OpenStreetMap tiles on the network you'll use.
5. Install the Python packages Person 1 lists, so you can run the backend locally.

---

## P2-0 · Kickoff, together (0:00–0:30)

Follow `plans/INTEGRATION.md` §2. Clone the repo and create branch `p2`.

---

## P2-1 · Frontend skeleton with fixture mode, plus a minimal ops router (0:30–1:30) → **Sync 1**

**Build: frontend (`web/`)**
- **Setup:**
  - Vite + React + TypeScript + Tailwind + react-router.
  - `vite.config.ts`:
    - A proxy sending `/api` to `http://localhost:8000`.
    - An alias `@contract` → `../contract`.
    - `server.fs.allow: ['..']`.
- **`src/api/client.ts`:** a typed fetch wrapper.
  - If `import.meta.env.VITE_USE_FIXTURES === 'true'`, return the JSON imported from `@contract/fixtures/*.json`, with a 300 ms fake delay.
  - Otherwise call `/api/...`.
  - **One function per endpoint** in contract §3.
- **`src/api/types.ts`:** hand-written TS types copied from the contract for now. They get replaced by `types.gen.ts` at Sync 1 via `npm run gen:types` (`openapi-typescript http://localhost:8000/openapi.json -o src/api/types.gen.ts`).
- **`src/i18n.ts`:** a small dictionary for UI labels in Tamil and English, with a toggle in the header.
  - Issue messages already arrive bilingual from the API, so don't translate those.
  - Load the **Noto Sans Tamil** and **Inter** fonts, with a system-font fallback.
- **Layout:**
  - A top bar with the logo text "SevaiCheck", the nav (Counter · Officer · Admin · Metrics · Report Issue) and the language toggle.
  - A clean, trustworthy government look: white/off-white surfaces, one deep blue accent and status colours (green accepted, amber fixable, red invalid).
  - Full dark-mode support isn't needed.
- **Counter page (`/counter`), first version:** an upload box that calls `validateDocument(file, declaredType)` and renders the **ResultCard** component:
  - The status badge.
  - Each citizen-audience issue with **Tamil large + English below**.
  - A "Retake" button.
  - A latency chip ("Checked in 0.4 s", from `timings_ms.total`).
  - The extracted fields when accepted.

**Build: minimal ops backend (`engine/app/ops/`)**
- **`__init__.py`** exports `router` (an APIRouter) and `async def startup()`. Person 1's `main.py` auto-mounts them.
- **`offices.py`:** the office list below, inserted into the `Office` table on startup if it's empty.
- **`GET /offices`.**

**Offices** (approximate coordinates, fine for a demo map):

| id | name | type | taluk | lat | lng |
|---|---|---|---|---|---|
| off_cbe_north_to | Taluk Office – Coimbatore North | taluk_office | Coimbatore North | 11.040 | 76.950 |
| off_gandhipuram_es | e-Sevai Centre – Gandhipuram | esevai_centre | Coimbatore North | 11.017 | 76.968 |
| off_saibaba_es | e-Sevai Centre – Saibaba Colony | esevai_centre | Coimbatore North | 11.025 | 76.940 |
| off_cbe_south_to | Taluk Office – Coimbatore South | taluk_office | Coimbatore South | 10.990 | 76.962 |
| off_podanur_es | e-Sevai Centre – Podanur | esevai_centre | Coimbatore South | 10.965 | 76.980 |
| off_perur_to | Taluk Office – Perur | taluk_office | Perur | 10.975 | 76.915 |
| off_madukkarai_to | Taluk Office – Madukkarai | taluk_office | Madukkarai | 10.906 | 76.960 |
| off_sulur_to | Taluk Office – Sulur | taluk_office | Sulur | 11.024 | 77.125 |
| off_sulur_es1 | e-Sevai Centre – Sulur 1 | esevai_centre | Sulur | 11.030 | 77.118 |
| off_sulur_es2 | e-Sevai Centre – Sulur 2 | esevai_centre | Sulur | 11.0247 | 77.1256 |
| off_annur_to | Taluk Office – Annur | taluk_office | Annur | 11.232 | 77.105 |
| off_mtp_to | Taluk Office – Mettupalayam | taluk_office | Mettupalayam | 11.299 | 76.935 |
| off_mtp_es | e-Sevai Centre – Mettupalayam | esevai_centre | Mettupalayam | 11.305 | 76.942 |
| off_pollachi_to | Taluk Office – Pollachi | taluk_office | Pollachi | 10.658 | 77.008 |
| off_pollachi_es | e-Sevai Centre – Pollachi | esevai_centre | Pollachi | 10.662 | 77.012 |
| off_kinathu_to | Taluk Office – Kinathukadavu | taluk_office | Kinathukadavu | 10.822 | 77.017 |
| off_anaimalai_to | Taluk Office – Anaimalai | taluk_office | Anaimalai | 10.583 | 76.938 |
| off_valparai_to | Taluk Office – Valparai | taluk_office | Valparai | 10.327 | 76.955 |

**Done when:**
- `VITE_USE_FIXTURES=true npm run dev` shows the counter page rendering all three validate fixtures. Add a debug dropdown to switch between them; remove it later.
- `GET /api/offices` works when the backend runs.
- Then go to **Sync 1**: switch to the real API and generate types.

---

## P2-2 · Applications flow: backend and frontend (1:30–4:00) → **Sync 2**

**Build: ops backend**
- **`routers/applications.py`:** `POST /applications`, `GET /applications`, `GET /applications/{id}` and `PATCH /applications/{id}`.
  - `sla_due_at` is `created_at` + 72 h, and `sla_hours_left` is computed at read time.
  - **List sorting:** `ready_for_officer` first, then by ascending `sla_hours_left`.
- **`routers/documents.py`:** `POST /applications/{id}/documents`.
  1. Read the bytes and call `validate_image(bytes, declared_type)`.
  2. Create the `Document` row (`issues_json`, `fields_json`, `aadhaar_hmac`, `phash`) and call `save_image(doc_id, outcome.card_jpeg)` if it isn't `None`.
  3. Call `find_duplicates(...)`. If there are hits, append a `DUPLICATE_SUSPECTED` issue to the document, using Person 1's `make_issue` from `app.validation.messages`. This is a read-only import, which is allowed.
  4. Collect the latest document of each type and call `check_consistency([...extracted])`.
  5. Recompute the AppStatus with `ops/status.py` (the contract §1 rule). If the same `doc_type` was uploaded again after a non-accepted upload, increment `resubmissions`.
  6. Write an `AppEvent`.
  7. If the new status is `needs_fix`, create a **Notification** (mock SMS) with `body_en`/`body_ta` built from the blocking issues' messages.
  8. Return `{document_id, validation (with document_id set), application, consistency}`.
- **`GET /documents/{id}/image`:** `load_image`, or 404.
- **`PATCH` actions:**
  - `approve` and `reject` set the decision, call `delete_image` for all of the application's documents (the privacy rule), add an event and send a notification.
  - `reject` requires a `reason_code`.
  - `request_fix` sets the status to `needs_fix` and sends a notification.
- **`GET /notifications`.**
- **`engine/tests/ops/test_status.py`:** status-rule tests (missing back → `needs_fix`, all accepted → `ready_for_officer`, and so on).

**Build: frontend**
- **Counter page, full flow** (mobile-first, because this is the demo's star screen):
  1. **Operator bar:** an office select (remembered in localStorage, with try/catch) plus the citizen name, phone and service → **Create application**.
  2. **Document checklist:** three slots: Aadhaar front, Aadhaar back, and a PAN/Voter ID toggle.
     - Each slot uses `<input type="file" accept="image/jpeg,image/png" capture="environment">`, which opens the camera on phones and a file picker on laptops.
     - Each slot shows its own ResultCard and keeps a retake history: "Attempt 1: BLUR → Attempt 2: accepted".
  3. **Application panel:**
     - The status chip.
     - The consistency result: names side by side with the tier badge. `likely_match` shows "Officer will confirm".
     - `AADHAAR_BACK_MISSING` and any other application-level issues.
     - When the status is `ready_for_officer`, a big green "Sent to officer ✓".
  4. **Phone mock panel:** a phone frame on the right (below on mobile) listing notifications for this application, polled every 3 s.
- **Officer page (`/officer`):**
  - **Queue table:** status, citizen, office, service, flag chips, SLA countdown (red if negative, amber if under 12 h) and doc count.
  - **Filters:** status and office.
  - **Click a row to open a drawer containing:**
    - Each document's image (`/api/documents/{id}/image`), fields, and issues with an expandable `evidence`.
    - The consistency card.
    - The history timeline.
    - Actions: Approve, Request fix (choose a reason code from a select) and Reject (requires a reason and a note).
  - After an action, show a toast and refresh.

**Done when:**
- **The full loop works with Person 1's real validation (post-Sync 2):** create an application, upload 01 (BLUR, fixable), then 02 (accepted), 03 and 05. The status becomes `ready_for_officer`, it appears first in the officer queue, approve it, and the images are deleted.
- `smoke_test.py` passes.

---

## P2-3 · Operational data, alerts and admin dashboard (4:00–6:30) → **Sync 3**

**Build: seed (`ops/seed.py`, run as `python -m app.ops.seed --reset`)**
- **`--reset`** drops non-office rows and deletes `DATA_DIR/images/*`.
- **30 days of historical records** ending now, about 2,000 applications, all with `is_seed=true` and no images. They represent officer-review outcomes *before* SevaiCheck.
- **Daily volume per office:** Poisson(taluk office 10, e-Sevai 6). Applications are created during business hours (9:30–17:30 IST, stored in UTC).
- **Each application** has 3 documents (Aadhaar front, Aadhaar back, PAN or Voter ID).
- **Baseline issue probabilities per application:**
  - BLUR 9%, GLARE 6%, AADHAAR_BACK_MISSING 5%, CROPPED 4%, TOO_DARK 3%
  - LOW_RESOLUTION 2%, NAME_MISMATCH 2%, DOB_MISMATCH 1%, INVALID_CHECKSUM 1%
- An application with a blocking issue gets a resubmission 1–4 days later. 70% of resubmissions are fixed on the second try.
- **Officer decision time:** lognormal, median 30 h.
- **Planted stories.** Each one must be produced by the data, not by hardcoded alerts:
  - **A (Sulur 2 scanner):** in the last 7 days, `off_sulur_es2` BLUR probability is 35%, versus 10% before.
  - **B (Pollachi backlog):** in the last 6 days, decision times at `off_pollachi_to` are 5× longer, so 20+ `ready_for_officer` applications are past the SLA.
  - **C (duplicate):** one Aadhaar HMAC appears in 3 applications at 3 different centres in the last 10 days. Compute it with Person 1's `aadhaar_hmac()` on a fake number.
  - **D (user reports):** 4 `scanner_problem` IssueReports at `off_sulur_es2` in the last 24 h, plus 6 random other reports across the month.
- Also seed fake **historical** document rows with `issues_json`, so `by_issue` counts work.

**Build: alerts (`ops/alerts.py`)**
- **`evaluate_rules(session, now)`** runs all the rules, upserting by `dedupe_key` (rule + office + code + ISO week). It runs in `startup()`, then every 60 s via an asyncio background task.
- **Rules** (thresholds in `ops/alert_rules.json`, every number in the text computed):
  - **`REJECT_SPIKE`:** per office and code, the 7-day rate is more than `2.0` × the previous 7-day rate, with `n_now ≥ 20`. Severity is high if the ratio is at least 3.
  - **`SLA_BREACH`:** an office has ≥ 5 applications with `sla_hours_left < 0` that aren't decided.
  - **`BACKLOG_GROWTH`:** an office's open backlog grew on each of the last 3 days.
  - **`DUPLICATE_CLUSTER`:** the same `aadhaar_hmac` appears in ≥ 2 applications.
  - **`USER_REPORTED`:** ≥ 3 reports of the same category for one office in 24 h.
- **`suggested_action_en`** comes from a per-rule/per-code map. For example, BLUR: "Check scanner/camera focus; brief operators on holding cards steady." GLARE: "Use diffuse lighting or a matte surface; avoid overhead tube lights."
- **Endpoints:** `GET /alerts` and `POST /alerts/{id}/ack`.
- **Issue reports:** `POST /issues` and `GET /issues`. A new report re-runs the `USER_REPORTED` rule immediately.

**Build: ops metrics (`ops/metrics_ops.py`)**
- `GET /metrics/operations?days=30` in the contract shape.
  - `first_time_right_rate` is the share of applications with no blocking issue on the first upload.
  - `backlog` is the count of undecided applications at the end of each day.
- **`projection`:**
  - Fetch recall per code with `from app.routers.metrics_detection import load_detection_metrics` (a read-only import).
  - `prevented = Σ rejections_with_code × recall(code)` over counter-detectable codes (the quality codes, `AADHAAR_BACK_MISSING` and `INVALID_CHECKSUM`).
  - `assumptions_en` spells out the formula and states the data is synthetic.

**Build: Admin page (`/admin`)**
- A banner: "Synthetic operational data (seeded) — for demonstration".
- **KPI cards:** applications (30 d), first-time-right rate, average resubmissions, backlog now and SLA breaches now.
- **Leaflet map:**
  - Centre 11.0, 76.96, zoom 9.
  - A circle marker per office, with the radius scaled by backlog and the colour by reject rate (green < 15%, amber 15–25%, red > 25%).
  - The popup shows the stats and the top issue.
  - If tiles fail to load, the markers still render.
- **Alerts panel:** severity badge, title, detail, evidence and suggested action, with an **Acknowledge** button. Newest first.
- **Charts:**
  - Daily submitted/approved/rejected/backlog lines (Recharts).
  - Issues by code (bar).
  - A sortable office table.
- **Recent issue reports** list.
- **Report Issue page (`/report`):** office, category, role and description → submit → toast. Also link it from the counter page ("Report a problem at this centre").

**Done when:**
- After `seed --reset`, the admin page shows all four stories as alerts, with the numbers computed.
- Submitting a 4th scanner report for another office creates a new `USER_REPORTED` alert within a minute.
- Then go to **Sync 3**.

---

## P2-4 · Metrics page, polish and slides (6:30–8:00)

- **Metrics page (`/metrics`):**
  - **Detection:**
    - A source badge. If `source == "FIXTURE"`, show a red "placeholder numbers" warning.
    - A per-code P/R/F1/support table, field accuracy and latency p50/p95.
    - A **highlighted card for `false_invalid_rate`**: "Genuine cards wrongly marked invalid".
    - The consistency confusion matrix as a 3×3 grid.
    - The dataset note.
  - **Effectiveness:** a baseline vs projected reject-rate bar, the prevented rejections and the assumptions text, always visible.
- **Polish:**
  - Loading skeletons, empty states and error toasts.
  - The counter page works on a phone-width screen.
  - Remove the debug dropdown.
  - Consistent spacing and type.
  - The favicon and page title.
- **Stretch, only if done by 7:30:**
  - `GET /reports/weekly.pdf` with reportlab: KPIs, top issues, alerts and the office table.
  - A "Download weekly report" button on the admin page.
- **Start the slides** (7 slides):
  1. The rejection loop (a diagram).
  2. The insight: catch errors at the counter.
  3. The live demo (a placeholder slide).
  4. How it works (the pipeline diagram from Person 1).
  5. Accuracy on held-out data (from `results.json` only).
  6. Impact: the projection plus root-cause analytics, using the Sulur scanner story.
  7. Privacy by design plus next steps (a pilot at one taluk, real-capture validation, Tamil OCR).

**Done when:**
- The metrics page shows `source: evaluation` numbers.
- The app looks finished on a laptop and a phone.
- Then **feature freeze at 8:00**.

---

## P2-5 · Final phase (8:00–11:00)

Follow `plans/INTEGRATION.md` §5–§7. Your specific jobs:
- Bug fixes in your folders only.
- **`README.md`** (everything except the Engine and Evaluation sections):
  - What it is.
  - Screenshots, saved to `docs/screenshots/`.
  - Quick start.
  - The architecture diagram (Mermaid).
  - Features.
  - Privacy.
  - The team.
- **`demo/demo_script.md`:** the exact clicks and words, about 3 minutes.
- Record the backup video.
- **You drive the UI during the demo.**
