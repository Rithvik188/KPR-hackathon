# Handoff: login/hierarchy/Notices/CAN round (in progress, stopped for session limit)

Person 2's Claude session hit its usage limit mid-feature. This is exactly where it stopped, what's done and
tested, and what's left, so anyone (Person 1, Person 2 next session, or the human) can pick it up without
re-deriving the plan. Nothing here is merged to `main` — it's committed on `p2` only.

## What the human asked for (verbatim intent)

1. Department login: a unique login parameter (staff ID) + CAPTCHA, differentiating VAO / RI / Tahsildar /
   govt e-Sevai operator / private e-Sevai operator, with **hierarchy preserved structurally** (a VAO must not
   be able to act as RI or Tahsildar — not just hidden in the UI, actually impossible once signed in).
2. Both operator types get citizen-portal-like access **minus Track application**, **plus a Notices tab**
   showing alerts/warnings from admin for their own office (reusing our existing alert engine).
3. Check whether CAN (Citizen Access Number) is implemented anywhere — it wasn't (only mentioned in
   `README.md`'s "how it works today" research). Proposed implementing it properly: a persistent citizen
   profile, name/DOB locked after creation, reused across applications.
4. Citizen login: add an OTP step (mock), and double-check citizens can't reach department/operator routes.
5. List other documents we could verify as reliably as Aadhaar/PAN/Voter ID.
6. **Coordinate with Person 1 over the `comms` git branch** wherever the change touches their files.

## Already sent to Person 1 (comms branch, `p2-to-p1/0006-can-and-centre-type-proposal.md`)

Proposing, additive, contract v1.5:
- A new `Citizen` (CAN) table in `engine/app/core/models.py` (**P1's file** — needs their sign-off/implementation,
  or they review a draft from us): `id` (the CAN), `name`, `dob`, `phone` (unique), `address_line`, `pin_code`,
  `created_at`. Immutable after creation. `Application.can_id: str | None` FK, with `citizen_name`/`citizen_dob`
  kept as a display cache populated from the CAN at creation (so nothing downstream breaks). `check_consistency`
  signature is unaffected — we'd just source `form.name`/`form.dob` from the CAN record instead of free text.
- **Check comms for their reply before touching `models.py` or `contract/` yourself** — those are their files.

Also flagged as informational (no action needed from P1 tonight): Driving Licence and Passport are the only
two other ID types with a fixed, checkable format (no checksum, so `INVALID_FORMAT` tier like PAN/EPIC, not
`INVALID_CHECKSUM` tier like Aadhaar). Everything else (ration card, MGNREGA job card, marksheets, birth/death
registration numbers) has no national format to validate — stays at the existing "supporting document" tier
(page quality + keyword, `CONTENT_NOT_VERIFIED`).

**Check `git show origin/comms:p1-to-p2/` for anything newer than `#0006` before continuing** — Person 1 may
have replied.

## Done and tested, on branch `p2` (not yet committed — see "To commit" below)

All of this is backend-only additive (no P1 files touched) or pure frontend; type-check and build both pass;
targeted tests pass (`pytest tests/ops/test_offices.py tests/ops/test_seed_alerts.py
tests/ops/test_seed_robustness.py` — 12 passed). The full suite was **not** re-run (explicit instruction this
session: skip full test suites, this is a polish/fixes pass).

1. **`engine/app/ops/alerts.py`**: `GET /alerts` now takes an optional `office_id` filter — this is what the
   Notices tab will call. `web/src/api/client.ts`'s `listAlerts()` already takes a matching second param.
2. **`engine/app/ops/offices.py`**: a new `OfficeType` value `esevai_centre_private` is seeded on 3 of the 8
   e-Sevai centres (Saibaba Colony, Sulur 1, Pollachi) to model the real govt-vs-private-franchise split P1's
   README research found (~6,000 govt, ~26,500 private). **`Office.type` is a plain `str` column, no DB enum**,
   so this needed zero changes to P1's `models.py`. The seeded demo-story offices (Sulur 2, Gandhipuram,
   Podanur, Mettupalayam e-Sevai) were deliberately left as plain `esevai_centre` so the four alert stories are
   untouched. `engine/app/ops/schemas.py`'s `OfficeType` literal and `web/src/api/types.ts`'s `OfficeType` both
   updated to match. `engine/app/ops/seed.py`'s `VOLUME` dict got the new key added (would otherwise `KeyError`
   and crash the whole seed script — this was the one real landmine in this change, already fixed and tested).
   **Still needed from P1**: one line in `contract/api.md` §1, `OfficeType` → add `esevai_centre_private` (their
   file; purely documentation, no behaviour depends on it).
3. **`web/src/pages/officer/OfficerPage.tsx`**: new optional `lockedRole?: Stage` prop. When set, the role
   selector becomes a static, non-interactive badge instead of clickable buttons — this is the actual hierarchy
   enforcement (a VAO literally cannot click "Tahsildar" anymore). When unset, behaves exactly as before.
4. **`web/src/v2/pages/department/DeptQueuePage.tsx`**: rewritten to pass `lockedRole={profile.role}` instead
   of writing to `localStorage` (the old mechanism didn't actually prevent clicking other stage buttons — this
   closes that gap).
5. **`web/src/v2/auth.tsx`**: rewritten. Added `OperatorProfile` (`kind: 'operator'`, `name`, `employeeId?`,
   `centreType: 'govt' | 'private'`, `officeId`, `officeName`) and `loginOperator()`. `DepartmentProfile` gained
   an optional `employeeId?: string` field. **`employeeId` is optional on purpose, as a TODO marker** — it
   should become required once `DepartmentLoginPage` actually collects one (see below). Nothing currently
   calls `loginOperator()` yet — the page that will doesn't exist.

## Not started — what's actually left

Build these in order; each is independent-ish but the login pages are the main unblocked work (no P1
dependency at all):

1. **Rewrite `web/src/v2/pages/DepartmentLoginPage.tsx`.** Currently it's the old free-dropdown version
   (name + a `<Select>` of VAO/RI/Tahsildar + a demo button) — that's the opposite of "hierarchy preserved,"
   since anyone can pick any role. Replace with:
   - A staff-ID text input, format `^(VAO|RI|TAH)-[A-Z]{3,}-\d{3}$` (e.g. `VAO-SULUR-014`). Parse the prefix
     client-side to derive the role live as they type (show "Signing in as: Village Administrative Officer"
     once it matches) — **the typed ID determines the role, there is no separate role picker**. That's what
     makes the hierarchy structural rather than a UI suggestion.
   - A simple mock CAPTCHA: generate a random `a + b = ?` on page load (e.g. `useState(() => ({a: rand, b:
     rand}))`), require the correct sum before "Sign in" enables. No external captcha service — this is a
     prototype, never add a real one.
   - On submit, call `loginDepartment({ name, employeeId, role })` — `role` comes from the regex match, never
     from a dropdown.
   - Keep one demo button (e.g. fills `VAO-SULUR-014`, name "S. Meena") for the live demo, but the demo button
     should still go through the same parse-and-confirm step, not bypass it.
2. **New `web/src/v2/pages/OperatorLoginPage.tsx`** (doesn't exist yet). Structure:
   - Name, staff ID (free text, just a min-length check — no role prefix needed here, see next point).
   - An office `<Select>` populated from `getOffices()`, **filtered to `type.startsWith('esevai_centre')`**.
     The selected office's own `type` field (`esevai_centre` vs `esevai_centre_private`) determines
     `centreType` automatically — display it back once chosen ("Signing in at a private e-Sevai centre").
   - Same mock CAPTCHA pattern as above.
   - `loginOperator({ name, employeeId, centreType, officeId, officeName })`.
   - Link it from `CitizenLoginPage`/`DepartmentLoginPage`'s "switch to X login" footer links, and from
     `LandingPage` if there's room (optional — at minimum reachable via a direct link from Department login).
3. **Operator portal shell + Notices page.**
   - Reuse `web/src/v2/pages/citizen/CitizenLayout.tsx` as the template, but the nav list **must not include
     Track application**, and **must include a new Notices item**.
   - Cleanest approach: don't modify `CitizenLayout` (citizens still need Track) — instead copy it to
     `web/src/v2/pages/operator/OperatorLayout.tsx` with the adjusted nav array, reusing `PortalHeader` /
     `PortalFooter` unchanged (they're already generic).
   - `web/src/v2/pages/operator/NoticesPage.tsx`: call `listAlerts(undefined, profile.officeId)` (operator's
     own office only — this is why the `office_id` filter was added to the backend in this round) and render
     them. You can mostly reuse `web/src/pages/admin/AlertsPanel.tsx`'s `AlertCard` presentation, but operators
     probably shouldn't get the Acknowledge button (that's an admin action) — render it read-only, or pass a
     prop to hide the button if you want to keep one shared component.
   - Reuse `HomePage.tsx`'s pattern for an operator home (same feature-card grid style), swapping "Track" for
     "Notices" and dropping the Apply-for-citizens link unless you want operators to also use the Apply flow
     on a citizen's behalf (the real e-Sevai system has operators fill forms for citizens at the counter —
     worth considering, but not requested explicitly; ask the human before building it, don't assume).
4. **Citizen login OTP step**, in `web/src/v2/pages/CitizenLoginPage.tsx`:
   - After phone is entered, a "Send OTP" step reveals a 6-digit code **directly in the UI** (e.g. a toast or
     inline note: "Demo OTP: 482913") — this is a prototype, never claim to send a real SMS. Require the
     citizen to re-type that code before "Sign in" is enabled. Keep the existing demo-account button as a
     bypass (it already skips credential entry entirely, consistent with the other demo buttons).
5. **Route wiring in `web/src/App.tsx`**: add `operator-login` route, an `operator/*` subtree gated by
   `<RequireAuth kind="operator" loginPath="/operator-login" />` wrapping `OperatorLayout`, with `index`
   (operator home) and `notices` children. Follow the exact pattern already used for `portal/*` and
   `department/*` in that file.
6. **i18n**: every new string above needs `en`/`ta` entries in `web/src/i18n.tsx`, following the existing
   `v2.*` key convention (e.g. `v2.operatorLogin.title`, `v2.notices.title`, `v2.login.otp`, `v2.login.captcha`,
   etc.) — look at how `v2.login.*` and `v2.dept.*` are already structured before adding new ones.
7. **CAN**, once P1 replies on comms: build the "create or find CAN" step at the start of
   `web/src/v2/pages/citizen/ApplyPage.tsx` (currently it creates the application straight from the logged-in
   citizen profile's free-text name/DOB — insert a CAN lookup/creation step before that, and source
   `citizen_name`/`citizen_dob` from the returned CAN record instead of the profile).
8. **Verify when done**: `npx tsc -p tsconfig.app.json --noEmit`, `npm run build`, then live in the browser —
   sign in as each of the 5 roles, confirm a VAO genuinely cannot reach RI/Tahsildar actions, confirm Notices
   shows only that operator's own office's alerts, confirm a citizen profile can't open `/department` or
   `/operator` (should already hold via `RequireAuth`, but re-check after adding the new route).

## Verification already done this session (don't redo)

- `npx tsc -p tsconfig.app.json --noEmit` — clean, after every edit in this round.
- `npm run build` — green.
- `pytest tests/ops/test_offices.py tests/ops/test_seed_alerts.py tests/ops/test_seed_robustness.py` — 12
  passed (confirms the new office type doesn't crash the seed script or break the four alert stories).
