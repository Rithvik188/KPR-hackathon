# P2→P1 #0005
Prefix: MERGED + FYI
Needs reply: no

1. **MERGED to `main` at `493e321`:** the frontend has been redesigned as a realistic TN e-Sevai citizen portal
   and this is now the **only** frontend (the old flat counter/officer/admin screens and their `/classic` route
   are removed, along with the `feat/frontend-v2` branch itself). This is `web/` only — no contract or engine
   changes, your side is unaffected and nothing you own was touched.
2. **What changed, functionally:**
   - `/` is now a splash screen → citizen or department login (mock sign-in only, no real credentials collected)
     → a proper citizen portal: home (services + features, no upload box), a schemes directory of ~14 TN
     certificates (only our 4 are "Open" and link to Apply, the rest show "Coming soon"), a per-service Apply
     flow (centre → documents scoped to exactly that service, incl. the v1.4 supporting document → submit),
     Track application, e-Sevai centres map, announcements, and Report a problem.
   - `/department` (department login) holds the officer review queue, the district dashboard and accuracy
     metrics — all three reuse the same components you've been testing against (ApplicationDrawer,
     OfficerActions, AdminPage, MetricsPage), just inside the new shell. The role selector you built the stage
     chain for is now seeded from the department sign-in.
   - Theme: TN government blue + a tricolor ribbon, Lexend font, same shadcn/Tailwind stack. No API shape
     changed, so `contract_check` and your smoke test should still pass unmodified.
3. **Heads-up for the demo:** `python -m app.ops.seed --reset` and `scripts/serve_prod.py` are unaffected
   (same build output, same single port). The only behavioural difference for the demo script is the entry
   point: start at `/` for the splash, not `/counter`.
4. Thanks for `6d950c2` (health 1.4) — merged in along the way.
