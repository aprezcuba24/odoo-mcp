"""Shared ASGI middleware for the MCP HTTP app."""

from __future__ import annotations

from starlette.middleware import Middleware

from .shop_key_middleware import ShopKeyMiddleware

MCP_HTTP_MIDDLEWARE: list[Middleware] = [Middleware(ShopKeyMiddleware)]
