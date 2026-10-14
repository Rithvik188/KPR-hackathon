"""POST /applications/{id}/documents (validate, store, consistency, status, SMS) and GET /documents/{id}/image."""
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import Response
from sqlmodel import Session

from app.core.db import get_session
from app.core.errors import api_error
from app.core.models import Document, new_id
from app.ops.clock import now
from app.core.storage import load_image, save_image
from app.ops.notifications import notify_needs_fix, notify_ready
from app.ops.offices import office_names
from app.ops.schemas import UploadResultOut
from app.ops.service import DECIDED, add_event, blocking_issues, documents_of, get_app, recompute, summary
from app.ops.status import latest_by_slot, slot_of
from app.validation.api import MAX_BYTES, find_duplicates, validate_image
from app.validation.messages import make_issue
from app.validation.types import DECLARABLE_TYPES, Issue

router = APIRouter(tags=["ops"])


def _upload_note(declared_type: str, status: str, issues: list[Issue]) -> str:
    """History line, e.g. 'aadhaar_front: fixable (BLUR)'."""
    codes = [i.code for i in issues if i.severity != "info"]
    return f"{declared_type}: {status}" + (f" ({', '.join(codes)})" if codes else "")


# Plain `def`: FastAPI runs it in the threadpool, so OCR never blocks the event loop.
@router.post("/applications/{app_id}/documents", response_model=UploadResultOut)
def upload_document(app_id: str, file: UploadFile = File(...), declared_type: str = Form(...),
                    session: Session = Depends(get_session)) -> UploadResultOut:
    if declared_type not in DECLARABLE_TYPES:
        raise api_error(400, "BAD_DECLARED_TYPE", f"declared_type must be one of {', '.join(DECLARABLE_TYPES)}")
    app = get_app(session, app_id)
    if app.status in DECIDED:
        raise api_error(409, "ALREADY_DECIDED", f"Application {app_id} is already {app.status}")

    # 1. Validate (Person 1's engine). Oversize files come back as a FILE_TOO_LARGE result, not an HTTP error.
    outcome = validate_image(file.file.read(MAX_BYTES + 1), declared_type)
    doc_id = new_id("doc")
    issues = list(outcome.result.issues)

    # 2. Duplicate check across other applications (officer-only warning; does not change the doc status).
    if outcome.aadhaar_hmac or outcome.phash:
        others = find_duplicates(session, outcome.aadhaar_hmac, outcome.phash, app.id)
        if others:
            issues.append(make_issue("DUPLICATE_SUSPECTED",
                                     {"other_applications": ", ".join(others[:5]), "matches": len(others)}))
    result = outcome.result.model_copy(update={"document_id": doc_id, "issues": issues})

    # 3. Resubmission: a new upload into a slot whose previous upload was not accepted.
    docs = documents_of(session, app.id)
    previous = latest_by_slot(docs).get(slot_of(declared_type))  # type: ignore[arg-type]
    if previous is not None and previous.status != "accepted":
        app.resubmissions += 1

    # 4. Store the document row and the encrypted, perspective-corrected card image.
    doc = Document(id=doc_id, application_id=app.id, doc_type=result.doc_type, declared_type=declared_type,
                   status=result.status, issues_json=json.dumps([i.model_dump() for i in issues]),
                   fields_json=json.dumps(result.fields) if result.fields is not None else None,
                   extracted_json=json.dumps(outcome.extracted.to_dict()) if outcome.extracted else None,
                   aadhaar_hmac=outcome.aadhaar_hmac, phash=outcome.phash, uploaded_at=now())
    if outcome.card_jpeg:
        doc.image_path = save_image(doc_id, outcome.card_jpeg)
    session.add(doc)
    docs.append(doc)

    # 5. Consistency across the latest document of each slot, then the AppStatus rule.
    old_status = app.status
    consistency = recompute(app, docs)
    app.updated_at = now()
    add_event(session, app.id, "document_uploaded", "operator", _upload_note(declared_type, result.status, issues))

    # 6. Notifications only on a transition (contract v1.1).
    if app.status == "needs_fix" and old_status != "needs_fix":
        notify_needs_fix(session, app, blocking_issues(docs, consistency))
    elif app.status == "ready_for_officer" and old_status != "ready_for_officer":
        add_event(session, app.id, "sent_to_officer", "system")
        notify_ready(session, app)

    session.add(app)
    session.commit()
    session.refresh(app)
    return UploadResultOut(document_id=doc_id, validation=result,
                           application=summary(app, office_names(session).get(app.office_id, app.office_id), docs),
                           consistency=consistency)


@router.get("/documents/{doc_id}/image", response_class=Response,
            responses={200: {"content": {"image/jpeg": {}}}, 404: {"description": "Deleted or never stored"}})
def document_image(doc_id: str, session: Session = Depends(get_session)) -> Response:
    doc = session.get(Document, doc_id)
    data = load_image(doc_id) if doc is not None and doc.image_path else None
    if data is None:
        raise api_error(404, "IMAGE_NOT_AVAILABLE", "Card image was deleted after the decision, or never stored")
    return Response(content=data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})
