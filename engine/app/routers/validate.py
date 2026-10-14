from fastapi import APIRouter, File, Form, UploadFile

from app.core.errors import api_error
from app.validation.api import MAX_BYTES, validate_image
from app.validation.types import DECLARABLE_TYPES, ValidationResult

router = APIRouter(tags=["engine"])


@router.post("/validate", response_model=ValidationResult)
def validate(file: UploadFile = File(...), declared_type: str | None = Form(None)) -> ValidationResult:
    # Plain `def`: FastAPI runs it in the threadpool so OCR never blocks the event loop.
    if declared_type in ("", "null"):
        declared_type = None
    if declared_type is not None and declared_type not in DECLARABLE_TYPES:
        raise api_error(400, "BAD_DECLARED_TYPE", f"declared_type must be one of {', '.join(DECLARABLE_TYPES)}")
    data = file.file.read(MAX_BYTES + 1)  # oversize -> FILE_TOO_LARGE result, not an HTTP error
    return validate_image(data, declared_type).result
