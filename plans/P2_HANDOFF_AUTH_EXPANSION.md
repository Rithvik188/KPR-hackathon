# Handoff: login/hierarchy/Notices/CAN round

**Status:** the UI half of this round is **done and verified** (session 2). What's still open is the CAN
round, which needs ops endpoints first (see "Still open" below). Nothing here is merged to `main` yet: P1's #0011
says the feature freeze (about 03:40) has passed, so this merges only if both humans agree and it passes the
smoke test + a phone click-through.

## What the human asked for (verbatim intent)

1. Department login: a unique login parameter (staff ID) + CAPTCHA, differentiating VAO / RI / Tahsildar /
   govt e-Sevai operator / private e-Sevai operator, with **hierarchy preserved structurally** (a VAO must not
   be able to act as RI or Tahsildar — not just hidden in the UI, actually impossible once signed in).
2. Both operator types get citizen-portal-like access **minus Track application**, **plus a Notices tab**
   showing alerts/warnings from admin for their own office (reusing our existing alert engine).
3. Implement CAN (Citizen Access Number) properly: a persistent citizen profile, name/DOB locked after
   creation, reused across applications.
4. Citizen login: add an OTP step (mock), and double-check citizens can't reach department/operator routes.
5. List other documents we could verify as reliably as Aadhaar/PAN/Voter ID (answered in comms #0006: only
   Driving Licence and Passport have a checkable format; P1 noted them as a future option).
6. Coordinate with Person 1 over the `comms` git branch wherever the change touches their files.

## Done — session 1 (`p2` at `8d47450`)

- `engine/app/ops/alerts.py`: `GET /alerts?office_id=` filter (what Notices calls).
- `engine/app/ops/offices.py`: `esevai_centre_private` on 3 of 8 e-Sevai centres (Saibaba Colony, Sulur 1,
  Pollachi). The four seeded alert-story offices stay `esevai_centre`. `schemas.py`, `seed.py` `VOLUME` and
  `web/src/api/types.ts` updated to match. P1 documented the value in contract v1.5.
- `web/src/pages/officer/OfficerPage.tsx`: `lockedRole` prop renders the stage as a static badge.
- `web/src/v2/pages/department/DeptQueuePage.tsx`: passes `lockedRole={profile.role}`.

## Done — session 2 (UI only, on top of `8d47450` + `main` at `556d823`)

1. **`web/src/v2/auth.tsx`** — the hierarchy is enforced here, not in the pages:
   - `roleFromStaffId()`: `^(VAO|RI|TAH)-[A-Z]{3,}-\d{3}$` → `vao` / `ri` / `tahsildar`. `loginDepartment()`
     takes only `{name, employeeId}` and derives the role itself, so no caller can pass a role.
   - `centreTypeOf(office)`: `esevai_centre` → govt, `esevai_centre_private` → private. `loginOperator()` takes
     the `Office` and derives `centreType`, `officeId` and `officeName` from it. Non-e-Sevai offices are refused.
   - A stored profile is dropped on load if its role doesn't match its staff ID. That covers a hand-edited
     localStorage entry (VAO ID with `role: tahsildar`) and old profiles from the free role picker.
   - `employeeId` is now required on department and operator profiles.
2. **`DepartmentLoginPage.tsx`**: rewritten. Name + staff ID (auto-uppercased) + CAPTCHA, **no role picker**.
   It shows "Signing in as: <role>" live once the ID parses. Demo chips (`VAO-SULUR-014`, `RI-SULUR-007`,
   `TAH-SULUR-001`) fill name + ID, but you still answer the CAPTCHA.
3. **`OperatorLoginPage.tsx`** (new, `/operator-login`): name, operator ID (min 4 chars), and an e-Sevai centre
   picker (taluk offices excluded). It shows "Signing in at a government-run / private franchise centre" from
   the office's own type. Two demo chips, govt and private, pick the office from the live list by type (Sulur 2
   preferred for govt, because seeded data raises notices there), so they work in fixture mode and live.
4. **Operator portal** (`/operator/*`, gated by `RequireAuth kind="operator"`):
   - `OperatorLayout`: nav is Home, Notices, Schemes, Centres, News, Report. There is **no Track**, and
     `/operator/track` falls through to `/`.
   - `OperatorHomePage`: the centre card (name, operator ID, govt/private badge) and feature cards, with a live
     open-notice count on Notices.
   - `NoticesPage` + `useNotices`: `listAlerts(undefined, officeId)`, **also filtered client-side** by
     `office_id`, so an operator never sees another centre's alerts even if the server ignores the filter.
     Cards are read-only, with no Acknowledge button (that stays an admin action), and refresh every 30 s.
   - Reused citizen pages: Schemes, Centres, News, Report. `usePortalBase()` (`web/src/v2/portalBase.ts`) keeps
     their links inside the operator portal: breadcrumb home → `/operator`. Schemes hides the Apply buttons for
     operators and shows a note instead. The Report link pre-selects the operator's own office.
5. **`CitizenLoginPage.tsx`**: mock OTP. **Send OTP** validates the mobile number (`^[6-9]\d{9}$`), shows a
   6-digit demo code in the page ("No SMS is sent"), and locks the number. **Sign in** enables only once the
   code is re-typed. Also has **Get a new OTP** and **Change number**. The demo account button still bypasses.
6. **Shared pieces**:
   - `LoginShell.tsx` (banner, title, card, links to the other two sign-ins).
   - `MockCaptcha.tsx` (random `a + b`, checked in the browser only; never wire in a real captcha service).
   - The prototype banner is on every login page and in every portal header, as P1's #0010 asked.
7. **`PortalHeader`**: shows the staff ID next to the name for department staff.
8. **i18n**: every new string has `en` + `ta` (`v2.login.*`, `v2.operator.*`, `v2.notices.*`,
   `v2.home.noticesDesc`, `v2.services.operatorNote`). Alert text itself stays English (it comes from the rules
   engine).
9. `AlertsPanel.tsx` now exports `SEVERITY` and `compareAlerts`, so Notices sorts and colours alerts the same way.

### Verified (session 2)

- `npx tsc -p tsconfig.app.json --noEmit` clean, `npm run lint` 0 errors (warnings are the same kinds the
  existing code already has), `npm run build` green.
- **45/45 Playwright checks in fixture mode** (`npm run dev:fixtures`; no backend was run this session):
  - **Department:** bad ID rejected, no role picker, role derived from the ID, CAPTCHA gates sign-in, the queue
    shows a locked VAO badge with **zero** stage buttons, and tampered or legacy profiles are rejected.
  - **Operator:** govt and private both sign in, the nav has Notices and no Track, Notices shows only Sulur 2's
    alert (the fixture has 2 alerts, 1 for Sulur 2), no Acknowledge button, Schemes has no Apply, and the
    breadcrumb and Report links stay in `/operator`.
  - **Redirects:** an operator opening `/portal` or `/department` and a citizen opening `/operator` or
    `/department` are both sent to that portal's login.
  - **Citizen:** bad phone rejected, the OTP flow works, a wrong OTP is blocked, the demo bypass works.
  - **Other:** Tamil renders, no horizontal scroll at 390 px, no page errors.
- **Not yet done:** a run against the live backend + `scripts/smoke_test.py` + a phone click-through. That is
  needed before this goes to `main`.

## Still open

1. **CAN in the Apply flow — blocked on ops endpoints.** Contract v1.5 is on `main`. The UI step needs
   `POST /api/citizens` and `GET /api/citizens/{can}`, `can` on `POST /api/applications`, and `can_id` on
   ApplicationSummary/Detail. Until `can_id` is returned, contract_check reports 2 expected FAILs. The
   ownership table in `CLAUDE.md` puts `engine/app/ops/` under Person 2, but this session's human said P2 does
   frontend only. **The humans need to agree who builds these endpoints.** Once they exist, the UI work is:
   - add `Citizen` + `getCitizen`/`createCitizen` to `web/src/api/types.ts` / `client.ts` (and fixture mode,
     from `contract/fixtures/citizen.json`);
   - insert a "create or find CAN" step at the start of `web/src/v2/pages/citizen/ApplyPage.tsx`;
   - pass `can` on `createApplication`, and show the CAN (and that name/DOB are locked) on the track pages.
2. **Ask the human first:** should operators also fill the Apply flow on a citizen's behalf at the counter? Real
   e-Sevai works that way, but it wasn't requested, so the operator portal is reference-only for now.
3. **Before merging to `main`**:
   - run against the real backend: `python scripts/dev.py`, sign in as each of the 5 profiles, walk
     VAO → forward → RI → forward → Tahsildar → approve, and check that Notices for Sulur 2 shows the
     seeded rejection spike;
   - run `scripts/smoke_test.py`, `scripts/contract_check.py` and `pytest tests/ops`;
   - do a phone click-through.
