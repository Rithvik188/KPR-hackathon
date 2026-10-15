import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

from app.core.config import WEB_DIST_DIR, get_settings
from app.core.db import create_db
from app.core.errors import api_error, register_error_handlers
from app.core.policy import authorize
from app.routers import auth, health, metrics_detection, validate
from app.validation import start_ocr_warmup

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Ops hook: Person 2's package mounts itself, so Person 1 never edits app/ops/.
try:
    from app.ops import router as ops_router, startup as ops_startup
except ImportError:
    ops_router, ops_startup = None, None

settings = get_settings()
if settings.auth_required and not settings.staff_demo_password:
    raise RuntimeError("AUTH_REQUIRED=1 needs STAFF_DEMO_PASSWORD in .env (or set AUTH_REQUIRED=0 for local dev only)")
Image.MAX_IMAGE_PIXELS = 40_000_000  # decompression-bomb guard (a 12 MP phone photo is ~12 M pixels)
MAX_REQUEST_BYTES = 11 * 1024 * 1024


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db()
    if settings.ocr_warmup:
        start_ocr_warmup()  # background thread; /validate waits for it on first use
    if ops_startup:
        await ops_startup()
    yield


docs_on = settings.expose_api_docs or not settings.serve_web
app = FastAPI(title="SevaiCheck API", version=health.API_VERSION, lifespan=lifespan,
              docs_url="/docs" if docs_on else None, redoc_url=None, openapi_url="/openapi.json" if docs_on else None)

CSP = ("default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob: https://*.tile.openstreetmap.org; font-src 'self' data:; connect-src 'self'; "
       "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > MAX_REQUEST_BYTES:
        return JSONResponse({"error": {"code": "FILE_TOO_LARGE", "message": "Request too large (max 10 MB)"}},
                            status_code=413)
    response = await call_next(request)
    h = response.headers
    h["X-Content-Type-Options"] = "nosniff"
    h["X-Frame-Options"] = "DENY"
    h["Referrer-Policy"] = "no-referrer"
    h["Permissions-Policy"] = "camera=(self), microphone=(), geolocation=(), payment=()"
    h["Cross-Origin-Opener-Policy"] = "same-origin"
    h["Content-Security-Policy"] = CSP
    if request.headers.get("x-forwarded-proto") == "https" or request.url.scheme == "https":
        h["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith("/api/"):
        h["Cache-Control"] = "no-store"  # personal data must not sit in shared/browser caches
    return response


register_error_handlers(app)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])

guard = [Depends(authorize)]  # central permission table (app/core/policy.py) on every /api route
for r in (health.router, auth.router, validate.router, metrics_detection.router):
    app.include_router(r, prefix="/api", dependencies=guard)
if ops_router is not None:
    app.include_router(ops_router, prefix="/api", dependencies=guard)


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
