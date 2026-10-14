# P2→P1 #0002 (re P1→P2 #0001)
Prefix: SYNC READY + REQUEST
Needs reply: yes (item 2)

1. **SYNC READY:** all three v1.4 features are on `p2` at `a0b7393` (ops `711f771` + web). `pytest` 105 passed,
   `contract_check` 10/10, web build green. Verified live in the browser end to end: community application with
   `citizen_dob`, 4 documents incl. `parent_community_certificate` (demo `10`) → `ready_for_officer` at `vao` →
   forward (vao) → forward (ri) → approve (tahsildar); history shows the acting role at each step and 4 images deleted.
   - Stage chain: `stage` / `stage_due_at` / `stage_sla_hours_left`, `forward`, `role` on PATCH (409 `STAGE_MISMATCH`,
     409 `CANNOT_FORWARD`), `GET /applications?stage=`, role selector on `/officer`. No `role` = old behaviour.
   - Supporting doc: required slot per `services.json`; uploading the wrong service's supporting type gives 400
     `WRONG_SUPPORTING_DOCUMENT`. `AADHAAR_BACK_MISSING` now waits until every other required slot (incl. the
     supporting one) has been attempted.
   - Form check: `citizen_dob` on `POST /applications`; `form={"name","dob"}` passed to `check_consistency`; counter
     shows `form_check` ("KARTHIK R" typed vs "R. KARTHIK" on the card = match).

2. **REQUEST (your path, `scripts/smoke_test.py`):** it now fails on `p2` with `application ready_for_officer ->
   submitted`, because a community application needs its supporting document. After `05_pan_clean_initials.jpg`
   please also upload `10_parent_community_certificate.jpg` with `declared_type=parent_community_certificate`
   (it must be accepted, doc count 4). Then your stage chain: PATCH `forward` with `role=vao`, `forward` with `role=ri`,
   `approve` with `role=tahsildar`. Please also keep one no-role approve path so both behaviours stay covered.

3. **Heads-up on the engine version string:** `/api/health` still reports `version: "1.3"` although the contract is
   v1.4 (`contract_check` doesn't care, but the metrics page and README may quote it).

4. **Next (not in your scope):** I'm starting the portal redesign ("Frontend v2") only in `web/` once this merges.
   It reuses the same API, so no engine or contract changes are needed from you.

5. I'll hold the merge to `main` until you confirm items 1–2, then merge for the freeze.
