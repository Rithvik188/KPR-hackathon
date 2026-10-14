from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["engine"])

API_VERSION = "1.4"


@router.get("/health")
def health() -> dict:
    from app.validation import ocr_status  # late import: keeps /health cheap if OCR is still loading

    s = get_settings()
    st = ocr_status()
    return {"status": "ok", "ocr_engine": s.ocr_engine, "ocr_gpu": st["gpu"], "ocr_ready": st["ready"],
            "version": API_VERSION}
