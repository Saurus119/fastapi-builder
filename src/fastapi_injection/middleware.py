from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .container import Services, get_request_scope

if TYPE_CHECKING:
    from starlette.types import ASGIApp


class RequestScopeMiddleware(BaseHTTPMiddleware):
    """Middleware that manages request-scoped dependency injection."""

    def __init__(self, app: ASGIApp, services: Services) -> None:
        super().__init__(app)
        self.services = services

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Response],
    ) -> Response:
        """Handle request with scoped dependency injection context."""
        scope_var = get_request_scope()
        token = scope_var.set({})

        try:
            response = await call_next(request)
            return response
        finally:
            # Dispose scoped services (close DB sessions, etc.)
            self.services.dispose_scope()
            scope_var.reset(token)
