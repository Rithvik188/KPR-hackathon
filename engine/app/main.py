import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.core.config import WEB_DIST_DIR, get_settings
from app.core.db import create_db
from app.core.errors import api_error, register_error_handlers
from app.routers import health, metrics_detection, validate
from app.validation import start_ocr_warmup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Ops hook: Person 2's package mounts itself, so Person 1 never edits app/ops/.
try:
    from app.ops import router as ops_router, startup as ops_startup
except ImportError:
    ops_router, ops_startup = None, None

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db()
    if settings.ocr_warmup:
        start_ocr_warmup()  # background thread; /validate waits for it on first use
    if ops_startup:
        await ops_startup()
    yield


app = FastAPI(title="SevaiCheck API", version=health.API_VERSION, lifespan=lifespan)
register_error_handlers(app)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

for r in (health.router, validate.router, metrics_detection.router):
    app.include_router(r, prefix="/api")
if ops_router is not None:
    app.include_router(ops_router, prefix="/api")


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE"], include_in_schema=False)
def api_not_found(path: str):
    raise api_error(404, "NOT_FOUND", f"No API route /api/{path}")


if settings.serve_web:
    dist = WEB_DIST_DIR.resolve()
    if not (dist / "index.html").exists():
        raise RuntimeError(f"SERVE_WEB=1 but {dist}/index.html is missing; run `npm run build` in web/")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        candidate = (dist / path).resolve()
        if path and candidate.is_file() and dist in candidate.parents:
            return FileResponse(candidate)
        if path.startswith("assets/") or "." in path.rsplit("/", 1)[-1]:
            raise api_error(404, "NOT_FOUND", f"No file /{path}")  # missing asset: 404, not index.html
        return FileResponse(dist / "index.html")  # SPA fallback for client-side routes
