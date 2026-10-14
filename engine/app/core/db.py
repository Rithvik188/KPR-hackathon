"""SQLite engine, table creation and the FastAPI session dependency."""
from collections.abc import Iterator

from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine

from app.core import models  # noqa: F401  (registers tables on SQLModel.metadata)
from app.core.config import get_settings

_settings = get_settings()
engine = create_engine(_settings.db_url, connect_args={"check_same_thread": False, "timeout": 30})


@event.listens_for(engine, "connect")
def _sqlite_pragmas(dbapi_conn, _record) -> None:
    # WAL lets the alert background task read while a request writes.
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA busy_timeout=30000")
    cur.close()


def create_db() -> None:
    _settings.data_dir.mkdir(parents=True, exist_ok=True)
    _settings.images_dir.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
