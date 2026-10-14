"""Person 2's operations package. app.main mounts `router` under /api and awaits `startup()`."""
import asyncio

from fastapi import APIRouter

from app.ops import alerts, issues, metrics_ops, notifications, offices
from app.ops.routers import applications, documents

router = APIRouter()
for _r in (offices.router, applications.router, documents.router, notifications.router, alerts.router,
           issues.router, metrics_ops.router):
    router.include_router(_r)


async def startup() -> None:
    offices.startup()
    # First alert evaluation, then a daemon thread re-evaluates every interval_seconds (alert_rules.json).
    await asyncio.to_thread(alerts.start_background)
