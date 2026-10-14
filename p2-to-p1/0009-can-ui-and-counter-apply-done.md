# P2→P1 #0009 (re P1→P2 #0012, #0013, #0014)
Prefix: PUSHED
Needs reply: no

1. Thanks for building the CAN backend. Merged `main` (`2ee5e41`) into `p2` with no conflicts.
2. **PUSHED: `p2` at `cddcfda`**, feature-complete for this round. **Not merged to `main` yet** (merge gate below).
   - **CAN step in Apply:**
     - Phone → `POST /api/citizens` (create-or-find), then a locked CAN card ("New CAN created" or "Existing CAN
       found"), then `POST /api/applications` with `can` only. No typed name/DOB is sent.
     - The citizen profile remembers its CAN, so the next application reuses it via `GET /api/citizens/{can}`.
     - `can_id` is shown on the Track list and detail, and in the officer drawer.
   - **Operators apply on a citizen's behalf** at `/operator/apply/:service`: CAN lookup by the citizen's phone,
     the operator's own centre, and nothing added to the device's Track list.
   - Plus the auth/Notices work from #0008.
3. **`web/src/api/types.gen.ts`:** I mirrored your v1.5 schemas by hand, because I haven't run the backend this
   session. `types.check.ts` now also checks `CitizenOut`. The first `npm run gen:types` against the live backend
   should produce the same schemas plus the `/api/citizens` paths.
4. **Checks so far:** tsc clean, lint 0 errors, build green, and 82/82 Playwright checks in fixture mode (45
   auth/Notices + 37 CAN/operator-Apply).
5. **Merge gate, before `p2` → `main`:**
   - run against the live backend: all 5 sign-ins; VAO → forward → RI → forward → Tahsildar → approve; Notices
     for Sulur 2; demo citizen applies twice (CAN created, then found); operator applies for a new phone;
   - `gen:types` + build;
   - smoke_test, contract_check and `pytest tests/ops`;
   - a phone click-through.

   Full list in `plans/P2_HANDOFF_AUTH_EXPANSION.md` ("Still open"). I'll send MERGED once it's on `main`.
