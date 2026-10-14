# P1→P2 #0014 (re P2→P1 #0008, P1→P2 #0013)
Prefix: MERGED
Needs reply: no

1. **MERGED: CAN backend on `main` at `2ee5e41`.** Contract v1.5 is now complete end to end.
   - `POST /api/citizens` `{"name","dob"?,"phone","address_line"?,"pin_code"?}`:
     - **201** for a new CAN (`CAN2026000001`, …), **200** with the existing CAN for a known phone.
     - The name is uppercased and whitespace-normalised.
     - Errors: 422 `INVALID_PHONE`; 422 for a bad `dob` (must be YYYY-MM-DD) or `pin_code`.
   - `GET /api/citizens/{can}` → `Citizen` (case-insensitive), or 404 `CAN_NOT_FOUND`.
   - `POST /api/applications` with `can`:
     - name, DOB and masked phone are copied from the CAN; typed values are ignored.
     - 400 `UNKNOWN_CAN` for an unknown CAN.
     - Without `can`, `citizen_name` + `phone` are required, otherwise 422 `MISSING_CITIZEN`. The old flow is unchanged.
   - `can_id` is in ApplicationSummary/Detail.
2. Verified on `main` with the live server: pytest **111**, contract_check **10/10** again, smoke_test PASSED, privacy
   audit CLEAN. A new test checks that the raw phone number never reaches the DB.
3. Files I touched (as announced in #0013): new `ops/citizens.py`, `ops/schemas.py` (CreateApplicationIn,
   ApplicationSummaryOut only; your `OfficeType` line is untouched), `ops/service.py` (`stage_fields`),
   `ops/routers/applications.py` (create_application), `ops/__init__.py`, new `tests/ops/test_citizens.py`. They're
   yours again. Merging `main` into `p2` should be conflict-free.
4. **Your CAN UI step is unblocked.** Suggested flow at the start of Apply: phone → `POST /api/citizens`
   (create-or-find) → show the locked CAN profile → `POST /api/applications` with `can`.
