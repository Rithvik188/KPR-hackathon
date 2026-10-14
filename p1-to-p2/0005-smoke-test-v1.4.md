# P1→P2 #0005 (re P2→P1 #0001)
Prefix: MERGED
Needs reply: no

1. Thanks for the seed fix. Confirmed after `seed --reset` on `main`: exactly 4 alerts.
2. **MERGED:** `main` at `dc049ca`. `scripts/smoke_test.py` now (per your note #6):
   - creates a community-certificate application with `citizen_dob`
   - uploads 01 → 02 → 03 → 05 → **10_parent_community_certificate**
   - checks `form_check` (name_tier `match`, dob_match `true`)
   - runs the stage chain when `application.stage == "vao"`:
     1. approve as vao → **409**
     2. forward as vao → `ri`
     3. forward as vao again → **409**
     4. forward as ri → `tahsildar`
     5. approve as tahsildar → 200
   On a pre-v1.4 server those checks print SKIP. It passes on `main` today.
3. Please run it against `p2` before you send PUSHED. All checks should be PASS, with no SKIPs. Use the PATCH error
   code `STAGE_MISMATCH` (409) for a wrong role, and 409 too for approve/reject outside `tahsildar` when `role` is given.
