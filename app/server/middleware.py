"""HTTP middleware stack for the MCP endpoint."""

from __future__ import annotations

from starlette.middleware import Middleware

from .app_key_middleware import AppKeyMiddleware

MCP_HTTP_MIDDLEWARE: list[Middleware] = [Middleware(AppKeyMiddleware)]
