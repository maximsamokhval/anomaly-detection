"""Request/response logging middleware using Loguru."""

import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.infrastructure.logging import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log every request with method, path, status, and duration."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.monotonic()

        logger.debug(
            f"[{request_id}] → {request.method} {request.url.path}"
            + (f"?{request.url.query}" if request.url.query else "")
        )

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            logger.error(
                f"[{request_id}] ✗ {request.method} {request.url.path} — exception after {elapsed_ms}ms: {exc}"
            )
            raise

        elapsed_ms = int((time.monotonic() - start) * 1000)
        level = "WARNING" if response.status_code >= 400 else "DEBUG"
        logger.log(
            level,
            f"[{request_id}] ← {response.status_code} {request.method} {request.url.path} [{elapsed_ms}ms]",
        )

        return response
