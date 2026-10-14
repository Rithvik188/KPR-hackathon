"""All tunable numbers live in thresholds.json (written by evaluation.tune)."""
import json
from pathlib import Path

THRESHOLDS_PATH = Path(__file__).with_name("thresholds.json")

_cache: dict | None = None
_cache_mtime: float | None = None


def get_thresholds() -> dict:
    """Reloads automatically when tune rewrites the file."""
    global _cache, _cache_mtime
    mtime = THRESHOLDS_PATH.stat().st_mtime
    if _cache is None or mtime != _cache_mtime:
        _cache = json.loads(THRESHOLDS_PATH.read_text(encoding="utf-8"))
        _cache_mtime = mtime
    return _cache
