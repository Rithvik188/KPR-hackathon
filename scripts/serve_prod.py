"""Production mode: build web/, then serve UI + API from one port (8000) for ngrok.

Usage (repo root):  python scripts/serve_prod.py [--skip-build] [--port 8000]
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
WEB = ROOT / "web"


def venv_python() -> str:
    for p in (ENGINE / ".venv" / "Scripts" / "python.exe", ENGINE / ".venv" / "bin" / "python"):
        if p.exists():
            return str(p)
    return sys.executable


def main() -> int:
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else "8000"
    if not (ROOT / ".env").exists():
        print("! .env missing: copy .env.example to .env and fill the secrets")
        return 1
    if "--skip-build" not in sys.argv:
        if not shutil.which("npm"):
            print("! npm not found: install Node 20, or pass --skip-build if web/dist already exists")
            return 1
        for cmd in ("npm ci", "npm run build"):
            print(f"> {cmd}  (web/)")
            if subprocess.run(cmd, cwd=WEB, shell=True).returncode != 0:
                print(f"! `{cmd}` failed")
                return 1
    if not (WEB / "dist" / "index.html").exists():
        print("! web/dist/index.html missing")
        return 1
    env = {**os.environ, "SERVE_WEB": "1"}
    print(f"> serving UI + API on http://0.0.0.0:{port}  (Ctrl-C to stop; then `ngrok http 127.0.0.1:{port}`)")
    try:
        return subprocess.run([venv_python(), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
                              cwd=ENGINE, env=env).returncode
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
