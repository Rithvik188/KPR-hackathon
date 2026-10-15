"""Settings loaded from the repo-root .env. Missing or malformed secrets fail loudly at startup."""
from functools import lru_cache
from pathlib import Path

from cryptography.fernet import Fernet
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENGINE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = ENGINE_DIR.parent
CONTRACT_DIR = REPO_ROOT / "contract"
WEB_DIST_DIR = REPO_ROOT / "web" / "dist"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    aadhaar_hmac_secret: str
    image_enc_key: str
    database_url: str = ""
    data_dir: Path = ENGINE_DIR / "data"
    ocr_engine: str = "rapidocr"  # rapidocr | easyocr
    ocr_gpu: str = "auto"  # auto | 0 | 1
    ocr_warmup: bool = True
    serve_web: bool = False
    # Security (docs/SECURITY.md). Secure by default: every non-public API route needs a signed session token.
    auth_required: bool = True
    staff_demo_password: str = ""  # demo staff accounts' password; share privately, never shown in the UI
    demo_otp_in_response: bool = False  # prototype has no SMS gateway: return the OTP in the API response
    expose_api_docs: bool = False  # /docs and /openapi.json (dev only)

    @field_validator("aadhaar_hmac_secret")
    @classmethod
    def _secret_long_enough(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("AADHAAR_HMAC_SECRET must be at least 32 characters (use secrets.token_hex(32))")
        return v

    @field_validator("image_enc_key")
    @classmethod
    def _valid_fernet_key(cls, v: str) -> str:
        try:
            Fernet(v.encode())
        except Exception as exc:  # noqa: BLE001
            raise ValueError("IMAGE_ENC_KEY is not a valid Fernet key (use Fernet.generate_key())") from exc
        return v

    @field_validator("staff_demo_password")
    @classmethod
    def _strong_password(cls, v: str) -> str:
        if v and len(v) < 10:
            raise ValueError("STAFF_DEMO_PASSWORD must be at least 10 characters")
        return v

    @field_validator("data_dir")
    @classmethod
    def _absolute_data_dir(cls, v: Path) -> Path:
        # Relative paths are relative to engine/, so the app works from any cwd.
        return v if v.is_absolute() else (ENGINE_DIR / v).resolve()

    @field_validator("ocr_engine")
    @classmethod
    def _known_engine(cls, v: str) -> str:
        v = v.strip().lower()
        if v not in {"easyocr", "rapidocr"}:
            raise ValueError("OCR_ENGINE must be easyocr or rapidocr")
        return v

    @property
    def db_url(self) -> str:
        url = self.database_url
        if not url:
            return f"sqlite:///{(self.data_dir / 'sevaicheck.db').as_posix()}"
        prefix = "sqlite:///./"
        if url.startswith(prefix):
            return f"sqlite:///{(ENGINE_DIR / url[len(prefix):]).resolve().as_posix()}"
        return url

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
