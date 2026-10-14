# Integration Plan: Working Simultaneously and Assembling the Final Project

Both people read this file. It defines how two people and two Claude Code sessions build in parallel without blocking each other, how and when work is merged, and how the final, demo-ready project is produced.

---

## 1. The parallel-work model

You never wait for each other, because each phase has something real to build against:

| Phase | Person 2's frontend talks to | Person 2's ops code calls |
|---|---|---|
| 0:30–1:30 | Fixture JSON (`VITE_USE_FIXTURES=true`) | Nothing yet |
| 1:30–4:00 (after Sync 1) | The real backend | Person 1's **stub** `validate_image` / `check_consistency` / `find_duplicates` (contract shapes, fake values) |
| 4:00 onward (after Sync 2) | The real backend | Person 1's **real** functions. The signatures never changed, so no code changes |

Person 1 never touches the UI. Person 2 never touches validation. The contract (`contract/api.md`) and the Python interface (§4 of the contract) are the only coupling.

**If one person is blocked by the other:**
1. Don't wait. Stub the missing piece locally in your **own** folder. For example, Person 2 can temporarily return a hardcoded consistency result in `ops/` behind a `TODO(P1)` comment.
2. Send a `BLOCKED:` message (§3).
3. Remove the stub at the next sync.

---

## 2. Kickoff (0:00–0:30, together, on Person 1's laptop with Person 2 watching)

1. **Person 1 creates the repo:** GitHub → New repository `sevaicheck`, set to private for now. Add Person 2 as a collaborator.
2. **Person 1 seeds it** with this kit:
   ```bash
   git clone git@github.com:<you>/sevaicheck.git && cd sevaicheck
   # copy CLAUDE.md, contract/, plans/ from the kit into the repo root
   mkdir -p engine/app web scripts demo/images slides docs/screenshots
   git add -A && git commit -m "docs: kickoff kit (CLAUDE.md, contract v1.0, plans)"
   git push -u origin main
   git checkout -b p1 && git push -u origin p1
   ```
3. **Person 2:**
   ```bash
   git clone git@github.com:<you>/sevaicheck.git && cd sevaicheck
   git checkout -b p2 && git push -u origin p2
   ```
4. **Secrets.** Both use the same values, so seeded duplicate HMACs and encrypted images are interchangeable:
   ```bash
   python -c "import secrets; print('AADHAAR_HMAC_SECRET=' + secrets.token_hex(32))"
   python -c "from cryptography.fernet import Fernet; print('IMAGE_ENC_KEY=' + Fernet.generate_key().decode())"
   ```
   Put both in each person's `.env`, which is never committed. Share the values over a private DM.
5. **Read `contract/api.md` together for 10 minutes.** Change anything either of you dislikes **now**, while changes are free. Person 1 commits any edits with a `CONTRACT:` message.
6. **Agree on the communication channel** (§3) and set a shared timer for the sync points (§4).
7. Each person opens Claude Code in the repo root and pastes the start prompt from their plan.

---

## 3. Communication protocol

Use one chat thread (a WhatsApp/Slack DM is fine). Only these message types are needed:

| Prefix | Meaning | Example |
|---|---|---|
| `CONTRACT:` | The contract changed. Pull main after the next sync, or cherry-pick now | `CONTRACT: added optional fields.name_ta (v1.1)` |
| `PUSHED:` | Something the other person needs is on your branch | `PUSHED: models.py on p1, safe to cherry-pick` |
| `BLOCKED:` | You need something; say what you're doing meanwhile | `BLOCKED: need find_duplicates real; stubbing in ops for now` |
| `SYNC READY` | Your branch is committed and passes your "Done when" checks | |
| `MERGED` | Your merge to main is pushed | |
| `CUT:` | You're dropping a feature to protect the timeline | `CUT: PDF report` |

**Mid-phase cherry-pick:** use this when Person 2 needs Person 1's `models.py` at about 0:45, before Sync 1:
```bash
git fetch origin && git checkout p2 && git cherry-pick <commit-sha>
```
Only cherry-pick commits that touch the other person's owned files, so there's no conflict risk.

---

## 4. Sync points: exact procedure

Syncs are at **1:30, 4:00, 6:30, 8:00 (freeze) and 9:30 (release candidate)**. Each one is timeboxed to **15 minutes**. If a check fails and can't be fixed in 15 minutes, revert that merge commit (`git revert -m 1 <merge-sha>`), keep working, and retry at the next sync.

### 4.1 Merge sequence (identical at every sync)

**Person 1 merges first:**
```bash
git checkout p1 && git add -A && git commit -m "engine: <summary>" || true
git checkout main && git pull origin main
git merge --no-ff p1 -m "sync N: p1"
cd engine && pytest && cd ..
git push origin main
```
Then send `MERGED`.

**Person 2 merges second:**
```bash
git checkout p2 && git add -A && git commit -m "web/ops: <summary>" || true
git checkout main && git pull origin main
git merge --no-ff p2 -m "sync N: p2"
cd engine && pytest tests/ops && cd ..
cd web && npm run build && cd ..        # catches TS errors
git push origin main
```
Then send `MERGED`.

**Both bring main back into your branch:**
```bash
git checkout p1   # or p2
git merge main
git push
```

**Conflicts** should only happen in shared files (`README.md`, `.gitignore`, `requirements.txt`).
- `README.md`: keep both sections.
- `.gitignore`: union of both.
- `requirements.txt`: Person 1 owns it. Person 2 asks for additions via a `PUSHED:` message rather than editing.

Anything else conflicting means someone edited outside their folder. Find out why, then fix it.

### 4.2 Joint verification (both laptops, after both merges)

On **both** machines, from `main`:
```bash
./scripts/dev.sh
python scripts/contract_check.py
```

### 4.3 Acceptance checklist per sync

**Sync 1 (1:30): plumbing works**
- [ ] `GET /api/health` returns ok, and `/api/offices` returns 18 offices.
- [ ] `contract_check.py` passes for `/health`, `/validate`, `/metrics/detection` and `/offices`.
- [ ] The frontend, with `VITE_USE_FIXTURES=false`, uploads an image on `/counter` through the proxy and renders the stub result.
- [ ] `npm run gen:types` produces `types.gen.ts`, and `npm run build` passes.

**Sync 2 (4:00): the real engine is in the real flow**
- [ ] `demo/images/01_*` gives `fixable` + `BLUR` in under 1 s, on the counter page.
- [ ] `02_*`, `03_*` and `05_*` are accepted, with the masked Aadhaar shown.
- [ ] `08_*` is `invalid`. A low-quality version of a valid card is never `invalid`.
- [ ] Create application → 4 uploads → `ready_for_officer` → appears first on the officer page → image visible → approve → image deleted (the image endpoint returns 404).
- [ ] `scripts/smoke_test.py` passes, and `pytest` passes.

**Sync 3 (6:30): intelligence and operations**
- [ ] The officer drawer shows the consistency tiers: `05_*` with `02_*` shows **likely match** with `R→RAJENDRAN`, and `09_*` shows a **mismatch**.
- [ ] Uploading the same card into two applications shows `DUPLICATE_SUSPECTED` to the officer only.
- [ ] After `seed --reset`, the admin page shows the map, KPIs, charts and **all four story alerts**, each with computed numbers.
- [ ] A new issue report triggers `USER_REPORTED` within 60 s.
- [ ] The notifications panel shows the Tamil and English SMS for a `needs_fix` application.
- [ ] `thresholds.json` (tuned) is merged.
- [ ] `contract_check.py` passes for every endpoint.

**Sync 4 (8:00): feature freeze**
- [ ] `evaluation/results.json` exists with `source: "evaluation"`, and the metrics page shows it. No FIXTURE badge visible anywhere.
- [ ] The privacy grep is clean: no 12-digit runs in the DB, logs or API responses.
- [ ] Everything is merged. Tag it:
  ```bash
  git tag v0.9-freeze && git push --tags
  ```
- [ ] **From now on, no new features.** Only `fix/<name>` branches, merged after the other person says OK.

**Sync 5 (9:30): release candidate.** See §5. Tag `v1.0-rc`.

---

## 5. Final assembly (8:00–9:30): exact steps

Do these in order, and tick each one off.

### 5.1 Bug bash (8:00–8:40)
1. Swap roles. Person 1 uses the UI as an operator, an officer and an admin. Person 2 tries to break the engine with odd uploads: a PDF renamed to .jpg, a 12 MB file, a photo with no card, a sideways card, a tiny image.
2. Log each bug in `docs/bugs.md` with an owner (based on folder ownership) and a severity: **demo-blocking**, **visible** or **cosmetic**.
3. Fix demo-blocking bugs first, then visible ones. Skip cosmetic bugs unless they're trivial.

### 5.2 Production build (8:40–8:55, Person 1)
`scripts/serve_prod.sh` must do:
```bash
cd web && npm ci && npm run build && cd ..
cd engine && source .venv/bin/activate
SERVE_WEB=1 uvicorn app.main:app --host 0.0.0.0 --port 8000      # no --reload
```

**Verify:**
- `http://localhost:8000/` serves the UI.
- `/officer` survives a browser refresh (the SPA fallback works).
- `/api/health` works.
- Only **one port** is open.

### 5.3 Clean-room test (8:55–9:15, both)
**This is what makes it look like a professional project.**
1. On **Person 2's laptop**, clone into a brand-new folder. Follow **only** the README Quick Start: create `.env` from `.env.example`, install, seed, run eval, serve.
2. Every time the README is wrong or missing a step, fix the README, not the machine.
3. Both laptops can now run the full app independently. **Laptop 2 is the hot backup.**

### 5.4 Demo state and remote access (9:15–9:30)
1. **Seed fresh demo data:** `python -m app.ops.seed --reset`. All the stories are fresh, and the counter has no leftover test applications.
2. **Start the tunnel:** `ngrok http 8000`. Open the ngrok URL on a phone **over mobile data**, not venue Wi-Fi, and run the counter flow once.
   - If venue Wi-Fi blocks it, use a phone hotspot for the laptop.
3. **Tag the release candidate:**
   ```bash
   git tag v1.0-rc && git push --tags
   ```

### 5.5 Backup video and rehearsal (9:30–11:00)
1. **Record the full demo** (3 minutes) with the OS screen recorder, following `demo/demo_script.md`. Save it locally on both laptops, and on a USB drive if you have one.
2. **Finish the slides.** Paste real numbers from `results.json` and the admin page. Never use fixture numbers.
3. **Rehearse twice, with a timer.**
   - **Rehearsal 1:** run end to end, then note what dragged.
   - **Rehearsal 2:** run at final pace.
   - **Then do the Q&A drill (§7).**
4. **Final release:**
   - Final README screenshots in `docs/screenshots/`.
   - `git tag v1.0 && git push --tags`.
   - Make the repo public if the hackathon requires it.

---

## 6. Demo-day runbook

**Roles:**
- **Person 2 drives the UI.** Person 2 knows every screen.
- **Person 1 narrates** the "how it works" and accuracy parts, and takes technical questions.

**Before going on:**
- Laptop 1: `serve_prod.sh` running, and seed reset within the last 30 minutes.
- Browser tabs open: `/counter`, `/officer`, `/admin`, `/metrics`.
- The demo images folder open.
- Laptop 2: also running, as the backup.
- Backup video ready.

**Demo flow (about 3 minutes):**
1. **Problem (20 s):** the rejection loop slide.
2. **Counter (60 s):** create an application, then upload `01` → Tamil + English "blurry, retake" in 0.4 s. Upload `02` → accepted with a masked number. Upload `03` and `05` → "likely match, officer will confirm" → "Sent to officer ✓". Show the SMS mock.
3. **Officer (30 s):** the item is at the top of the queue. Open the drawer: names side by side, `R→RAJENDRAN`, DOB match. Approve, and mention "images deleted on decision".
4. **Admin (45 s):** the map shows Sulur 2 in red. The alert says blur up 3.4×, and operator scanner reports corroborate it. That points to a hardware fix, not more officers. Then show the Pollachi SLA breach and the duplicate cluster.
5. **Metrics (25 s):** held-out accuracy, **the false-invalid rate** and latency, plus the projected prevented rejections with the formula visible.
6. **Close (10 s):** privacy by design. It plugs into existing e-Sevai counters with no new hardware. Next step: a pilot at one taluk.

**If something fails live:**

| Failure | Action |
|---|---|
| An upload hangs for more than 5 s | Say "OCR warming up", retry once, then switch to Laptop 2 |
| The backend crashes | Switch to Laptop 2 (it's already running) |
| Map tiles don't load | The markers still render; say "offline map tiles", and carry on |
| Total failure | Play the backup video and narrate over it |

---

## 7. Q&A preparation (who answers what)

| Likely question | Owner | Core of the answer |
|---|---|---|
| Is the accuracy real or overfit? | P1 | Thresholds were tuned on one split with background set A. Results come from a held-out split with background set B. Look at the false-invalid rate. Limitation: synthetic data only, so real capture validation is the next step. |
| Why not a deep learning model? | P1 | Deterministic checks are explainable (every rejection shows a measured value and its threshold), fast on CPU and need no training data. A model could later replace any single check behind the same interface. |
| What if OCR misreads a real Aadhaar? | P1 | The confidence gate: low-confidence reads become "retake", never "invalid". |
| How do you protect Aadhaar data? | P1 | Masked display. HMAC with a server secret, not a plain hash (10¹² numbers is brute-forceable). Images are encrypted and deleted on decision. Aligned with UIDAI masking practice and the DPDP Act. |
| How do alerts work? Are they hardcoded? | P2 | Rules over the data (e.g. a 7-day rate over 2× the prior 7 days). Show `alert_rules.json`, and file a live issue report to trigger one. |
| How would this deploy for real? | P2 | A web app at existing e-Sevai counters, a phone camera or scanner as input, one server per district. Integrating with existing portals is future work. |
| Where do the impact numbers come from? | P2 | The projection formula on the metrics page: seeded rejections × measured recall per code. It's a projection, not a claim. |
| Does it support Tamil? | P2 | Every citizen message is bilingual. Tamil OCR is on the roadmap, since the fields needed are printed in English on these cards. |

---

## 8. Master timeline

| Time | Person 1 (Engine) | Person 2 (Product) | Joint |
|---|---|---|---|
| 0:00–0:30 | | | Kickoff (§2) |
| 0:30–1:30 | P1-1 skeleton, models (push by 0:45), stubs, scripts | P2-1 frontend + fixtures, offices router | |
| **1:30** | | | **Sync 1** |
| 1:30–2:20 | P1-2 synthetic data generator | P2-2 applications backend | |
| 2:20–3:05 | P1-3 quality checks | P2-2 counter flow UI | |
| 3:05–4:00 | P1-4 OCR, classify, extract, rules, tests | P2-2 officer page | |
| **4:00** | | | **Sync 2** |
| 4:00–5:15 | P1-5 consistency + duplicates | P2-3 seed + alert engine | |
| 5:15–6:30 | P1-6 threshold tuning, performance | P2-3 admin dashboard, report page, ops metrics | |
| **6:30** | | | **Sync 3** |
| 6:30–7:40 | P1-7 held-out eval, privacy audit | P2-4 metrics page, polish | |
| 7:00–8:00 | P1-8 Tamil stretch (only if ahead) | P2-4 PDF stretch (only if ahead), start slides | |
| **8:00** | | | **Freeze (Sync 4)** |
| 8:00–9:30 | Bug bash, production build, README engine sections | Bug bash, README, demo script | Clean-room test, demo state |
| **9:30** | | | **Release candidate (Sync 5)** |
| 9:30–11:00 | | | Backup video, slides, two rehearsals, Q&A drill, tag v1.0 |

**Cut order if behind** (announce with `CUT:`):
1. Tamil stretch
2. PDF report
3. `BACKLOG_GROWTH` rule
4. phash near-duplicates (keep HMAC)
5. Charts beyond the two main ones
6. Officer drawer history timeline

**Never cut:**
- The counter flow
- The confidence gate
- Held-out evaluation
- The four seeded stories
- The backup video
