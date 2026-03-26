from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import structlog

logger = structlog.get_logger()


class AppException(Exception):
    """Base application exception."""

    def __init__(self, message: str, status_code: int = 400, detail: str | None = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class NotFoundException(AppException):
    def __init__(self, resource: str, id: str | int):
        super().__init__(
            message=f"{resource} not found: {id}",
            status_code=404,
        )


class TaskAlreadyRunningException(AppException):
    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task {task_id} is already running",
            status_code=409,
        )


class LLMProviderException(AppException):
    def __init__(self, provider: str, detail: str):
        super().__init__(
            message=f"LLM provider error ({provider}): {detail}",
            status_code=502,
        )


def register_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("app_exception", message=exc.message, status_code=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
