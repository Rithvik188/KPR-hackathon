"""Person 2's operations package. app.main mounts `router` under /api and awaits `startup()`."""
from fastapi import APIRouter

from app.ops import offices

router = APIRouter()
router.include_router(offices.router)


async def startup() -> None:
    offices.startup()
