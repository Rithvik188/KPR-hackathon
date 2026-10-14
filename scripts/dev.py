"""Start backend (:8000, auto-reload on app/ only) and frontend (:5173). Ctrl-C stops both.

Usage (repo root):  python scripts/dev.py [--backend-only]
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
WEB = ROOT / "web"


def venv_python() -> str:
    win = ENGINE / ".venv" / "Scripts" / "python.exe"
    nix = ENGINE / ".venv" / "bin" / "python"
    for p in (win, nix):
        if p.exists():
            return str(p)
    print("! engine/.venv not found, using the current interpreter")
    return sys.executable


def kill_tree(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.send_signal(signal.SIGTERM)


def main() -> int:
    if not (ROOT / ".env").exists():
        print("! .env missing: copy .env.example to .env and fill the secrets (see plans/INTEGRATION.md)")
        return 1
    procs = []
    # --reload-dir app: datagen output, SQLite and images must NOT trigger reloads (each reload re-warms OCR).
    procs.append(subprocess.Popen([venv_python(), "-m", "uvicorn", "app.main:app", "--reload", "--reload-dir", "app",
                                   "--port", "8000"], cwd=ENGINE))
    if "--backend-only" not in sys.argv:
        if (WEB / "package.json").exists():
            procs.append(subprocess.Popen("npm run dev", cwd=WEB, shell=True))
        else:
            print("! web/package.json not found yet, starting backend only")
    try:
        while all(p.poll() is None for p in procs):
            time.sleep(0.5)
        print("! a process exited, stopping the others")
    except KeyboardInterrupt:
        pass
    finally:
        for p in procs:
            kill_tree(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
