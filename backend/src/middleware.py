"""
HTTP middleware for the TTS Reader backend.

Provides:
  - RequestIDMiddleware: Assigns a unique request ID to each request
    and includes it in the response headers. Also logs request timing.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a unique X-Request-ID to every request.

    If the incoming request already has an X-Request-ID header (e.g., from a
    reverse proxy), it is preserved. Otherwise, a new UUID is generated.

    The request ID is:
      - Added to the response headers
      - Injected into the logging context for correlation
      - Used to log request duration
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Use existing request ID or generate a new one
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # Store on request state for access in route handlers
        request.state.request_id = request_id

        start_time = time.monotonic()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s [%s] %.1fms",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
            )
            raise

        duration_ms = (time.monotonic() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id

        # Log the request (skip health checks to reduce noise)
        if request.url.path != "/api/health":
            logger.info(
                "%s %s -> %d [%s] %.1fms",
                request.method,
                request.url.path,
                response.status_code,
                request_id,
                duration_ms,
            )

        return response
