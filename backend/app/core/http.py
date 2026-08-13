"""HTTP-level operational helpers shared by the FastAPI application."""

import logging
import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings

logger = logging.getLogger("enterprise_crm.http")
_REQUEST_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,63}$")


class _RequestBodyTooLarge(Exception):
    """Internal signal used by the streaming request-size guard."""


class RequestBodyLimitMiddleware:
    """Enforce a body limit even when Content-Length is omitted/chunked."""

    def __init__(self, app: ASGIApp, *, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        received = 0
        response_started = False

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _RequestBodyTooLarge
            return message

        async def tracked_send(message: Message) -> None:
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _RequestBodyTooLarge:
            if response_started:
                raise
            response = JSONResponse(
                {"detail": "Request body is too large"},
                status_code=413,
                headers={"Cache-Control": "no-store"},
            )
            await response(scope, receive, send)


def _request_id(request: Request) -> str:
    provided = request.headers.get("x-request-id", "").strip()
    if provided and _REQUEST_ID.fullmatch(provided):
        return provided
    return str(uuid4())


def install_http_middleware(application: FastAPI, settings: Settings) -> None:
    """Install request limits, tracing and defensive response headers."""

    application.add_middleware(
        RequestBodyLimitMiddleware,
        max_bytes=settings.http_max_request_bytes,
    )

    @application.middleware("http")
    async def request_observability(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = _request_id(request)
        started = perf_counter()

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = -1
            if declared_size < 0:
                return JSONResponse(
                    {"detail": "Invalid Content-Length header"},
                    status_code=400,
                    headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
                )
            if declared_size > settings.http_max_request_bytes:
                return JSONResponse(
                    {"detail": "Request body is too large"},
                    status_code=413,
                    headers={"X-Request-ID": request_id, "Cache-Control": "no-store"},
                )
        try:
            response = await call_next(request)
        except Exception:
            elapsed_ms = (perf_counter() - started) * 1000
            logger.exception(
                "request failed method=%s path=%s request_id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                elapsed_ms,
            )
            raise

        elapsed_ms = (perf_counter() - started) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers.setdefault("Cache-Control", "no-store")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        logger.info(
            "request method=%s path=%s status=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            elapsed_ms,
        )
        return response
