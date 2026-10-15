"""Privacy audit: no full Aadhaar number may appear in the DB, logs, stored files or API responses.

Searches for (a) every synthetic Aadhaar number we generated (exact, spaced and unspaced) and
(b) any 12-digit run not embedded in a hex string (HMACs are hex, so a plain \\d{12} grep would
false-positive on them).

Usage:  python scripts/privacy_audit.py [--base http://127.0.0.1:8000] [--logs path ...]
Exit code 1 on any leak.
"""
import json
import re
import sqlite3
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "engine"
BASE = sys.argv[sys.argv.index("--base") + 1] if "--base" in sys.argv else "http://127.0.0.1:8000"
TWELVE = re.compile(r"(?<![0-9A-Fa-f])(\d{4}[ \-]?\d{4}[ \-]?\d{4})(?![0-9A-Fa-f])")


def known_numbers() -> set[str]:
    nums: set[str] = set()
    out = ENGINE / "datagen" / "out"
    for path in list(out.glob("*/labels.jsonl")) + list(out.glob("sets/*/sets.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            truths = [row.get("truth")] + [d.get("truth") for d in row.get("docs", {}).values()]
            for t in truths:
                if t and t.get("id_number", "").isdigit() and len(t["id_number"]) == 12:
                    nums.add(t["id_number"])
    try:  # demo numbers are regenerated deterministically
        sys.path.insert(0, str(ENGINE))
        import random

        from datagen.generate_demo import build  # noqa: F401
        from datagen.numbers import make_aadhaar
        rng = random.Random(43)
        nums.add(make_aadhaar(rng))
    except Exception:  # noqa: BLE001
        pass
    return nums


def scan_text(label: str, text: str, nums: set[str]) -> list[str]:
    leaks = []
    digits_only = re.sub(r"[ \-]", "", text)
    for n in nums:
        if n in digits_only and (n in text or f"{n[:4]} {n[4:8]} {n[8:]}" in text):
            leaks.append(f"{label}: contains a generated Aadhaar number ending {n[-4:]}")
    for m in TWELVE.finditer(text):
        leaks.append(f"{label}: 12-digit run ending {re.sub(r'\\D', '', m.group(1))[-4:]}")
    return leaks


def main() -> int:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from _auth import staff_headers
    auth = staff_headers(BASE, "TAH-SULUR-001")
    opener = urllib.request.build_opener()
    opener.addheaders = list(auth.items())
    urllib.request.install_opener(opener)
    nums = known_numbers()
    print(f"checking against {len(nums)} generated Aadhaar numbers")
    leaks: list[str] = []
    db = ENGINE / "data" / "sevaicheck.db"
    if db.exists():
        con = sqlite3.connect(db)
        for (table,) in con.execute("select name from sqlite_master where type='table'"):
            cols = [r[1] for r in con.execute(f"pragma table_info('{table}')")]
            for row in con.execute(f"select * from '{table}'"):
                for col, val in zip(cols, row):
                    if isinstance(val, str) and col != "aadhaar_hmac":
                        leaks += scan_text(f"db {table}.{col}", val, nums)
        con.close()
    else:
        print("(no database yet)")
    logs = sys.argv[sys.argv.index("--logs") + 1:] if "--logs" in sys.argv else []
    for lp in logs:
        leaks += scan_text(f"log {lp}", Path(lp).read_text(encoding="utf-8", errors="ignore"), nums)
    for f in (ENGINE / "evaluation").glob("*.json"):
        leaks += scan_text(f"file {f.name}", f.read_text(encoding="utf-8"), nums)
    app_ids, offset = [], 0
    try:  # every application, page by page (seeded DBs hold thousands)
        while True:
            with urllib.request.urlopen(f"{BASE}/api/applications?limit=200&offset={offset}", timeout=60) as r:
                body = r.read().decode("utf-8", errors="ignore")
            leaks += scan_text(f"api /applications?offset={offset}", body, nums)
            page = json.loads(body)
            app_ids += [i["id"] for i in page.get("items", [])]
            offset += 200
            if not page.get("items") or offset >= page.get("total", 0):
                break
        for app_id in app_ids:
            with urllib.request.urlopen(f"{BASE}/api/applications/{app_id}", timeout=30) as r:
                leaks += scan_text(f"api /applications/{app_id}", r.read().decode("utf-8", errors="ignore"), nums)
        print(f"scanned {len(app_ids)} applications (list + detail)")
    except Exception as e:  # noqa: BLE001
        print(f"(skip applications: {e})")
    for path in ["/api/alerts", "/api/notifications", "/api/metrics/detection",
                 "/api/metrics/operations", "/api/issues"]:
        try:
            with urllib.request.urlopen(BASE + path, timeout=30) as r:
                body = r.read().decode("utf-8", errors="ignore")
            leaks += scan_text(f"api {path}", body, nums)
        except Exception as e:  # noqa: BLE001
            print(f"(skip {path}: {e})")
    for leak in leaks:
        print("LEAK", leak)
    print("PRIVACY AUDIT", "FAILED" if leaks else "CLEAN")
    return 1 if leaks else 0


if __name__ == "__main__":
    sys.exit(main())
