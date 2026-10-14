import json

from fastapi import APIRouter

from app.core.config import CONTRACT_DIR, ENGINE_DIR

router = APIRouter(tags=["engine"])

RESULTS_PATH = ENGINE_DIR / "evaluation" / "results.json"
FIXTURE_PATH = CONTRACT_DIR / "fixtures" / "metrics_detection.json"


def load_detection_metrics() -> dict:
    """Held-out evaluation results, or the FIXTURE placeholder if evaluation has not run yet."""
    path = RESULTS_PATH if RESULTS_PATH.exists() else FIXTURE_PATH
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/metrics/detection")
def metrics_detection() -> dict:
    return load_detection_metrics()
