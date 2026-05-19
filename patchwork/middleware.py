"""Request/response middleware support for patchwork.

Middleware can inspect or modify requests before routing and
responses before they are sent to the client.
"""

from __future__ import annotations

from typing import Callable, List, Optional


class MiddlewareError(Exception):
    """Raised when a middleware component fails."""


class RequestContext:
    """Carries request data through the middleware chain."""

    def __init__(self, method: str, path: str, headers: dict, body: bytes):
        self.method = method.upper()
        self.path = path
        self.headers = dict(headers)
        self.body = body
        self.meta: dict = {}

    def __repr__(self) -> str:  # pragma: no cover
        return f"RequestContext({self.method} {self.path})"


class ResponseContext:
    """Carries response data through the middleware chain."""

    def __init__(self, status: int, headers: dict, body: str):
        self.status = status
        self.headers = dict(headers)
        self.body = body

    def __repr__(self) -> str:  # pragma: no cover
        return f"ResponseContext({self.status})"


MiddlewareCallable = Callable[[RequestContext], Optional[ResponseContext]]


class MiddlewareChain:
    """Ordered collection of middleware callables."""

    def __init__(self) -> None:
        self._middlewares: List[MiddlewareCallable] = []

    def add(self, fn: MiddlewareCallable) -> None:
        """Register a middleware function."""
        if not callable(fn):
            raise MiddlewareError(f"Middleware must be callable, got {type(fn)}")
        self._middlewares.append(fn)

    def process_request(self, ctx: RequestContext) -> Optional[ResponseContext]:
        """Run all middleware against *ctx*.

        If any middleware returns a ResponseContext the chain is short-circuited
        and that response is returned immediately (useful for auth rejection, etc.).
        Returns None when all middleware pass.
        """
        for mw in self._middlewares:
            try:
                result = mw(ctx)
            except Exception as exc:
                raise MiddlewareError(f"Middleware {mw.__name__!r} raised: {exc}") from exc
            if result is not None:
                return result
        return None

    def __len__(self) -> int:
        return len(self._middlewares)
