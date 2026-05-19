"""Built-in middleware functions shipped with patchwork.

Each function follows the MiddlewareCallable signature:
    (RequestContext) -> Optional[ResponseContext]
"""

from __future__ import annotations

import logging
import time
from typing import Container, Optional

from patchwork.middleware import RequestContext, ResponseContext

logger = logging.getLogger(__name__)


def logging_middleware(ctx: RequestContext) -> None:
    """Log every incoming request at DEBUG level."""
    logger.debug("[patchwork] %s %s", ctx.method, ctx.path)
    ctx.meta["request_start"] = time.monotonic()


def cors_middleware(ctx: RequestContext) -> Optional[ResponseContext]:
    """Return a 204 pre-flight response for OPTIONS requests."""
    if ctx.method == "OPTIONS":
        return ResponseContext(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                "Access-Control-Allow-Headers": "*",
                "Content-Length": "0",
            },
            body="",
        )
    return None


def make_api_key_middleware(valid_keys: Container[str], header: str = "X-Api-Key"):
    """Factory that returns a middleware enforcing a static API key.

    Args:
        valid_keys: Collection of accepted key strings.
        header: HTTP header name to inspect (default ``X-Api-Key``).
    """

    def api_key_middleware(ctx: RequestContext) -> Optional[ResponseContext]:
        key = ctx.headers.get(header, "")
        if key not in valid_keys:
            return ResponseContext(
                status=401,
                headers={"Content-Type": "application/json"},
                body='{"error": "Unauthorized"}',
            )
        return None

    api_key_middleware.__name__ = "api_key_middleware"
    return api_key_middleware
