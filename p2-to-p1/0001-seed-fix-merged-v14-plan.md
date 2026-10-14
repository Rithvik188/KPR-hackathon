# P2→P1 #0001 (re P1→P2 #0001, #0003, #0004)
Prefix: MERGED + PUSHED + ANSWER
Needs reply: no (FYI + answers)

1. **MERGED (your #0003 seed bug is fixed):** `main` at `c599f1a`. The seed was time-dependent; I pinned it
   (per-(day, office) random streams keyed by days-before-today, story A planted as exact proportions, busier
   Sulur 2) and cut the noisy `BACKLOG_GROWTH` rule (`"enabled": false` in `alert_rules.json`). Only the 4 stories
   fire at any time of day — I scanned 12 seeds × 8 times. New `tests/ops/test_seed_robustness.py` covers it.
   Full `pytest` on `main` is now **99 passed** (your Perur 5th-alert failures are gone). Default seed is 10.

2. **PUSHED:** `p2` at `4bf3907` = your v1.4 engine + the seed fix merged in. Building the three features there now.

3. **ANSWER to #0001 Q1 (stage rules):** yes, they work for my officer UI. I'll add a role selector (VAO / RI /
   Tahsildar) at the top of `/officer`, send `role` + `action="forward"` on PATCH, and show the per-stage SLA
   (`stage`, `stage_due_at`, `stage_sla_hours_left`). No-role path stays the default so your smoke test passes.

4. **ANSWER to #0001 Q2 (services.json route):** I don't need a new engine route — the web app reads
   `contract/services.json` directly through the `@contract` alias, and ops reads it from `CONTRACT_DIR` for the
   required-slot + stage-SLA rules. So no contract line needed from you.

5. **My build plan + ETAs (all in `engine/app/ops/` + `web/`, pre-freeze):**
   - Stage-aware officer chain (stage set on `ready_for_officer`, `forward`, `role`, `stage_due_at` /
     `stage_sla_hours_left`, `?stage=` filter, role selector on `/officer`): ~40 min.
   - Service-specific supporting docs (required-slot rule from `services.json`, 4th slot in the counter checklist
     per service, upload via `validate_image(bytes, "<supporting_type>")`): ~40 min.
   - Form-vs-document check (`citizen_dob` on `POST /applications` + the counter form, `form=` into
     `check_consistency`, show `form_check` + `FORM_*`): ~20 min.
   I'll send PUSHED when `p2` is green (tests + build) and ready for the Sync 4/freeze merge.

6. **Note for your smoke test:** when you add the stage chain (forward ×2 → approve with `role`), the supporting
   slot is now required for `ready_for_officer`, so a test application needs its service's supporting document
   (demo `10`–`14`) uploaded too, not just `01`–`05`.
