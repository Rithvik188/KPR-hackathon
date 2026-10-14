"""Encrypted-at-rest card images (Fernet). Deleted when an application is decided."""
import re
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings

_SAFE_ID = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
_fernet = Fernet(get_settings().image_enc_key.encode())


def _path(document_id: str) -> Path:
    if not _SAFE_ID.match(document_id):
        raise ValueError(f"unsafe document id: {document_id!r}")
    return get_settings().images_dir / f"{document_id}.bin"


def save_image(document_id: str, jpeg_bytes: bytes) -> str:
    path = _path(document_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(_fernet.encrypt(jpeg_bytes))
    tmp.replace(path)
    return str(path)


def load_image(document_id: str) -> bytes | None:
    try:
        path = _path(document_id)
    except ValueError:
        return None
    if not path.exists():
        return None
    try:
        return _fernet.decrypt(path.read_bytes())
    except InvalidToken:
        return None  # written with a different IMAGE_ENC_KEY


def delete_image(document_id: str) -> None:
    try:
        _path(document_id).unlink(missing_ok=True)
    except ValueError:
        pass
