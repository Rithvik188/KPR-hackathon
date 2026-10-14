"""Duplicate detection: exact keyed-HMAC match on the Aadhaar number, or a near-identical card image."""
import imagehash
from sqlmodel import Session, select

from app.core.models import Document
from app.validation.thresholds import get_thresholds


def phash_distance(a: str, b: str) -> int:
    return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)


def find_duplicates(session: Session, aadhaar_hmac: str | None, phash: str | None,
                    exclude_application_id: str) -> list[str]:
    """Other application ids holding the same Aadhaar (HMAC) or a near-identical card photo (phash)."""
    hits: set[str] = set()
    if aadhaar_hmac:
        rows = session.exec(select(Document.application_id).where(
            Document.aadhaar_hmac == aadhaar_hmac, Document.application_id != exclude_application_id)).all()
        hits.update(rows)
    max_d = get_thresholds().get("phash_max_distance", -1)
    if phash and max_d >= 0:
        rows = session.exec(select(Document.application_id, Document.phash).where(
            Document.phash.is_not(None), Document.application_id != exclude_application_id)).all()
        for app_id, other in rows:
            try:
                if phash_distance(phash, other) <= max_d:
                    hits.add(app_id)
            except ValueError:
                continue
    return sorted(hits)
