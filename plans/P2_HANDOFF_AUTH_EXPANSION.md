# Handoff: login/hierarchy/Notices/CAN round

**Status:** **merged to `main`** ("sync: p2 - auth/hierarchy/Notices, CAN UI, operator counter Apply"). It
includes auth/hierarchy/Notices and the CAN UI + operator counter Apply.

- **Verified before the merge:** fixture-mode UI checks (82/82 Playwright), and P1's API half of the gate on
  `cddcfda` (#0015: pytest 111, contract_check 10/10, smoke_test passed, SPA routes 200).
- **The merge was done at the P2 human's request before the live browser + phone check.** That check is with
  P1 (comms P2→P1 #0010), see "Still open". If it finds a demo-blocking bug: fix forward on `p2`, or
  `git revert -m 1 <merge-sha>` on `main`.

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

## Done — CAN round (UI only, on top of P1's CAN backend, `main` at `2ee5e41`)

P1 built the CAN ops endpoints by agreement (comms #0013/#0014). On our side:

1. **API layer:**
   - `types.ts` has `Citizen`, `CitizenInput`, `can_id` on ApplicationSummary, and `can` on
     CreateApplicationInput.
   - `client.ts` has `createOrFindCitizen()`, which returns `{citizen, created}` (201 vs 200), and `getCitizen()`,
     both with fixture-mode answers. In fixture mode a phone ending `21` "already has" `CAN2026000123`.
   - `types.gen.ts` mirrors P1's v1.5 schemas by hand, because no backend was run this session.
     `types.check.ts` gains a `CitizenOut`/`Citizen` drift check. **Run `npm run gen:types` against the live
     backend once**: it should produce the same schemas, plus the `/api/citizens` paths.
2. **`CanStep.tsx`** (shared): the form is phone, name (as on Aadhaar), DOB, and optional address/PIN, then
   **Find or create CAN**. It then shows a locked CAN card (CAN, name and DOB with lock icons, masked phone,
   address) with a "New CAN created" or "Existing CAN found" badge. For an existing CAN whose name differs
   from what was typed, it says the CAN's own name/DOB are used.
3. **Citizen Apply** (`ApplyPage.tsx`):
   - The CAN step comes first. Phone is the signed-in number (read-only), and name/DOB are prefilled from login.
   - Then the centre, then `createApplication({can, service, office_id})`. No typed name/DOB is sent, so the
     certificate prints exactly what the CAN holds.
   - The CAN is remembered on the citizen profile (`auth.rememberCan`), so the next application shows the
     card straight away.
   - The CAN appears beside the uploads, on the submitted screen, in the Track list and on Track detail
     ("certificate name … (locked)").
4. **Operator counter Apply** (`/operator/apply/:service`, same `ApplyPage`):
   - The Schemes page shows Apply buttons for operators.
   - The CAN step starts empty, with an editable phone and **Use a different mobile number**.
   - The centre is fixed to the operator's own office.
   - Submitting doesn't add to this device's Track list, and the confirmation tells the operator to give the
     citizen the application number.
   - The operator home has an "Apply for a citizen" card.
5. **Officer drawer** shows `CAN …` in the application header.
6. **i18n:** `v2.can.*`, `v2.apply.operator*`/`newApplication`/`centreFixed`, `v2.home.applyForCitizen*`, and
   `v2.track.detail.canLocked`, all in `en` + `ta`.

### Verified (CAN round)

- tsc clean, lint 0 errors, build green.
- **37/37 Playwright checks in fixture mode:**
  - **CAN form:** comes first, phone locked to the login, bad PIN blocked.
  - **Existing CAN:** the card says found, warns that the typed name isn't used, saves the CAN to the profile,
    and the CAN shows beside the uploads, on the submitted screen, in the Track list and on Track detail. The
    next application reuses the CAN without the form.
  - **Operator:** a new CAN is created with a normalised name, the centre is fixed, the operator can switch
    number, submitting gives no Track link, and the device's Track list is unchanged.
  - **Officer drawer** shows the CAN.
  - **Other:** Tamil renders, no horizontal scroll at 390 px, no page errors.
- The 45-check auth suite was rerun: 45/45. One check was updated on purpose, because operators now have Apply
  buttons.

## Still open

1. **Live check on `main`, requested from P1** (comms #0010). Needs the real backend:
   - `python -m app.ops.seed --reset`, then `python scripts/dev.py`, and sign in as each of the 5 profiles;
   - walk VAO → forward → RI → forward → Tahsildar → approve;
   - check that Notices for Sulur 2 shows the seeded rejection spike;
   - apply with the demo citizen: the CAN gets created, then shown straight away on the second application;
   - apply as an operator for a new phone number;
   - run `scripts/privacy_audit.py`;
   - do a phone click-through over ngrok.
2. **`npm run gen:types`** against the live backend, then commit `web/src/api/types.gen.ts` (additions only, per
   #0015).
3. **Before the demo** (`plans/INTEGRATION.md` §5):
   - `demo/demo_script.md` (with the new sign-in steps), the README sections owed by P2 + `docs/screenshots/`,
     and the slides;
   - bug bash, clean-room test, fresh seed, ngrok, `v1.0-rc` tag, backup video, rehearsal, `v1.0` tag.
