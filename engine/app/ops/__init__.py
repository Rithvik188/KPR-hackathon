"""Person 2's operations package. app.main mounts `router` under /api and awaits `startup()`."""
from fastapi import APIRouter

from app.ops import notifications, offices
from app.ops.routers import applications, documents

router = APIRouter()
for _r in (offices.router, applications.router, documents.router, notifications.router):
    router.include_router(_r)


async def startup() -> None:
    offices.startup()
