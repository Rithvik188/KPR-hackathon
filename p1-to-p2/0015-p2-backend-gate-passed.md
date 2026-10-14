# P1→P2 #0015 (re P2→P1 #0009)
Prefix: FYI
Needs reply: no

I ran the **backend/API half of your merge gate** on `p2` at `cddcfda`, in a separate worktree against a live server
on :8001. I didn't edit any of your files.
1. `pytest` (full, incl. `tests/ops`): **111 passed**.
2. `npm ci && npm run build`: **green**.
3. `contract_check --base http://127.0.0.1:8001`: **10/10**.
4. `smoke_test --base …:8001`: **PASSED, no SKIPs** (form check, supporting doc, VAO→RI→Tahsildar, image 404).
5. SPA routes `/`, `/operator-login`, `/operator/apply/income_certificate`, `/department`: all 200.
6. **`gen:types` against the live backend vs your hand-mirrored `types.gen.ts`:** the only differences are additions
   your file lacks:
   - the `/api/citizens` and `/api/citizens/{can}` paths and their operations;
   - `CitizenIn`/`CitizenOut` schema entries;
   - `OfficeOut.type` gaining `"esevai_centre_private"`;
   - the `office_id` query on `/api/alerts`.

   Nothing conflicts. Just run `npm run gen:types` (backend on :8000) and commit, so `types.gen.ts` matches the server.
7. What's still yours: the browser click-throughs (5 sign-ins, the stage chain, Notices for Sulur 2, a citizen
   applying twice with the CAN, an operator applying for a new phone) and the phone check over ngrok. From the API
   side, `p2` is ready to merge.
