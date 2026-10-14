"""Contract error shape: {"error": {"code": "...", "message": "..."}}."""
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

_DEFAULT_CODES = {400: "BAD_REQUEST", 404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED", 409: "CONFLICT",
                  413: "FILE_TOO_LARGE", 422: "VALIDATION_ERROR", 500: "INTERNAL_ERROR"}


def api_error(status_code: int, code: str, message: str) -> HTTPException:
    """`raise api_error(404, "APPLICATION_NOT_FOUND", "No such application")`."""
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http(_: Request, exc: StarletteHTTPException):
        if isinstance(exc.detail, dict) and "code" in exc.detail:
            body = _body(exc.detail["code"], exc.detail.get("message", ""))
        else:
            body = _body(_DEFAULT_CODES.get(exc.status_code, f"HTTP_{exc.status_code}"), str(exc.detail))
        return JSONResponse(body, status_code=exc.status_code, headers=getattr(exc, "headers", None))

    @app.exception_handler(RequestValidationError)
    async def _validation(_: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        where = ".".join(str(p) for p in first.get("loc", []))
        return JSONResponse(_body("VALIDATION_ERROR", f"{where}: {first.get('msg', 'invalid request')}"),
                            status_code=422)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception):
        return JSONResponse(_body("INTERNAL_ERROR", type(exc).__name__), status_code=500)
