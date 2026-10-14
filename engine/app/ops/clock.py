"""Timezone-aware UTC "now" for ops.

SQLModel's datetime columns reject naive values on write and return aware UTC on read, so ops always passes
aware datetimes explicitly (never relying on a model's default_factory).
"""
from datetime import UTC, datetime


def now() -> datetime:
    return datetime.now(UTC)
