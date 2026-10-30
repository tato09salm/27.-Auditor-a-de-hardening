"""Middlewares de trazabilidad y endurecimiento HTTP."""

from __future__ import annotations

import re
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings

REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{8,80}$")
MAX_BODY_BYTES = 2 * 1024 * 1024


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get("X-Request-ID", "")
        request_id = incoming if REQUEST_ID_RE.match(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id

        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_BODY_BYTES:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "La solicitud excede el tamaño permitido."},
                        headers={"X-Request-ID": request_id},
                    )
            except ValueError:
                return JSONResponse(
                    status_code=400,
                    content={"detail": "Encabezado Content-Length inválido."},
                    headers={"X-Request-ID": request_id},
                )

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = response.headers.get(
            "Cache-Control", "no-store"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
        )
        if settings.environment == "production" and request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response
