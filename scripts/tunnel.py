"""Public HTTPS link for the demo: start (or reuse) an ngrok tunnel to the local server and print its URL.

Usage (repo root, server already running via scripts/serve_prod.py):  python scripts/tunnel.py [--port 8000]

Robust on Windows:
- finds ngrok even when the terminal's PATH is stale (winget installs it under %LOCALAPPDATA%);
- reuses an already-running tunnel instead of failing (the free plan allows one agent session at a time);
- points at 127.0.0.1, not localhost (Windows resolves localhost to IPv6 first, which adds about 2 s per request).
Keep this window open: closing it stops the tunnel.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

PORT = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8000"
API = "http://127.0.0.1:4040/api/tunnels"


def find_ngrok() -> str | None:
    found = shutil.which("ngrok")
    if found:
        return found
    local = os.environ.get("LOCALAPPDATA", "")
    patterns = [os.path.join(local, "Microsoft", "WindowsApps", "ngrok.exe"),
                os.path.join(local, "Microsoft", "WinGet", "Links", "ngrok.exe"),
                os.path.join(local, "Microsoft", "WinGet", "Packages", "Ngrok.Ngrok*", "ngrok.exe"),
                r"C:\ProgramData\chocolatey\bin\ngrok.exe"]
    for pattern in patterns:
        hits = glob.glob(pattern)
        if hits:
            return hits[0]
    return None


def running_url() -> str | None:
    try:
        with urllib.request.urlopen(API, timeout=2) as r:
            tunnels = json.loads(r.read()).get("tunnels", [])
    except Exception:  # noqa: BLE001
        return None
    for t in tunnels:
        if t.get("public_url", "").startswith("https://"):
            return t["public_url"]
    return None


def main() -> int:
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"! Nothing is answering on port {PORT}. Start the app first: python scripts/serve_prod.py")
        return 1
    url = running_url()
    if url:
        print(f"Tunnel already running (reusing it):\n\n    {url}\n")
        return 0
    exe = find_ngrok()
    if not exe:
        print("! ngrok not found. Install it:  winget install --id Ngrok.Ngrok   then   ngrok config add-authtoken <token>")
        return 1
    proc = subprocess.Popen([exe, "http", f"127.0.0.1:{PORT}", "--log", "stdout"], stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    for _ in range(30):
        time.sleep(0.5)
        url = running_url()
        if url:
            break
        if proc.poll() is not None:
            out = proc.stdout.read() if proc.stdout else ""
            err = next((ln for ln in out.splitlines() if "ERR_NGROK" in ln or "ERROR" in ln), out[-300:])
            print(f"! ngrok exited: {err}")
            if "too old" in out:
                print(f"  Fix: \"{exe}\" update")
            if "authtoken" in out.lower():
                print("  Fix: ngrok config add-authtoken <your token from dashboard.ngrok.com>")
            return 1
    if not url:
        print("! ngrok started but no tunnel appeared; check http://127.0.0.1:4040")
        return 1
    print(f"Public link (open on the phone over mobile data, tap 'Visit Site'):\n\n    {url}\n")
    print("Keep this window open. Ctrl-C stops the tunnel.")
    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
