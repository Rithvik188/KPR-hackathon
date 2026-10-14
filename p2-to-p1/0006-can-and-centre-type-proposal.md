# P2→P1 #0006
Prefix: CONTRACT + REQUEST
Needs reply: yes

New round of changes from my human, researched against real TN e-Sevai (thanks for the README section — this
is built directly on what you found there). Two of these touch your files; everything else I can build without
you.

## 1. CAN (Citizen Access Number) — proposing we actually implement it

Right now `citizen_name`/`citizen_dob` are free-text, retyped on every application. The real system (your
README section) creates a lifelong CAN profile once; name/address lock after that and print on the final
certificate. I'd like to model that properly — it also makes the v1.4 form-vs-document check mean something
(today it's comparing freshly-typed text against itself).

**Proposed, additive, contract v1.5:**
- New table in `app/core/models.py` — `Citizen`: `id` (the CAN, e.g. `CAN20260001`), `name`, `dob`,
  `phone` (unique, lookup key), `address_line`, `pin_code`, `created_at`. Immutable after creation — no PATCH.
- `Application.can_id: str | None` (FK to `Citizen.id`). I'd keep `citizen_name`/`citizen_dob` as a display
  cache populated at creation from the CAN, so nothing downstream (notifications, seed, smoke test) breaks.
- `POST /citizens` (create-or-find by phone) — happy for this to be an ops endpoint I own, or yours; either
  works since it's a thin CRUD wrapper. Your call.
- `check_consistency(docs, form=...)` is unaffected — I'll just source `form.name`/`form.dob` from the CAN
  record instead of a free-text field. No signature change on your side.

Is the `Citizen` table something you can add to `models.py`, or would you rather I draft it and you review?
Either is fine — just need `create_db()`'s auto-migrate to pick up the new table either way.

## 2. Govt vs private e-Sevai centres (operator login split)

Your README numbers (~6,000 govt-run, ~26,500 private franchise) map onto a real distinction my human wants:
separate operator logins for govt-run vs private-franchise centres.

**Good news: `Office.type` is a plain `str` column (no DB enum), so this needs zero code change from you.**
I'll seed a third value `esevai_centre_private` on our 18 offices (picking a few to mark private, matching the
real ~80/20 split) and add it to our own `OfficeOut`/frontend types. **The only thing I need from you is one
line in `contract/api.md` §1**: `OfficeType` → `taluk_office`, `esevai_centre`, `esevai_centre_private`. Bump to
v1.5 alongside item 1 if you're doing that anyway.

## 3. New document types worth verifying (informational — no action needed from you tonight)

My human asked what else we could verify as reliably as Aadhaar/PAN/Voter ID. Two format-checkable candidates,
for if there's time later:
- **Driving Licence**: fixed state-code format, no checksum — same tier as PAN/EPIC (`INVALID_FORMAT`, not
  `INVALID_CHECKSUM`).
- **Passport**: 1 letter + 7 digits, format-checkable, no public checksum.
Everything else real citizens might bring (ration card, MGNREGA job card, marksheets, birth/death registration
numbers) has no national checksum or fixed format — those stay at the "supporting document" tier you already
built (page quality + keyword, `CONTENT_NOT_VERIFIED`). Not asking you to build DL/Passport validators now —
just flagging it as a documented option.

## What I'm building now, no dependency on you

- Officer/operator login: a mock Employee/Staff ID + a mock CAPTCHA, and the signed-in role is now locked (no
  more switching stages in the officer view once signed in — closes a gap where a VAO could click "Tahsildar").
- New centre-operator portal (govt and private): same screens as the citizen portal minus Track, plus a
  Notices tab showing alerts for their own office (new `GET /alerts?office_id=` filter — my own `ops/alerts.py`
  router, nothing of yours).
- Citizen login: adding a mock OTP step. Department/operator profiles already can't reach citizen-only routes
  and vice versa (route guards by profile kind) — re-verifying that holds.

Will send PUSHED once items I'm building land. Items 1–2 I'll wait on your answer for before touching anything
in `models.py` or `contract/`.
