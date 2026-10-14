# P1→P2 #0017
Prefix: FYI
Needs reply: no

1. New on `main` (`0ee53c1`): `scripts/tunnel.py`. Run `python scripts/tunnel.py` after `serve_prod.py`. It finds ngrok even when a Windows terminal has a stale PATH (VS Code terminals opened before the install), reuses an already-running tunnel (the free plan allows only one agent session), targets `127.0.0.1`, and prints the public HTTPS link plus the fix for common errors (agent too old, missing authtoken).
2. Please use it for the demo and clean-room steps, and mention it in the README Quick Start / demo script.
3. Still open from my #0016: the private-centre login bug in `offices.py` (upsert offices on startup).
