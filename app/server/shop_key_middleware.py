"""Resolve shop-key once per HTTP request and attach it to request state."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.exceptions import (
    AmbiguousShopKeyError,
    InvalidShopKeyError,
    MissingShopKeyError,
)
from app.utils.shop_key_codec import SHOP_CONTEXT_STATE_KEY, parse_shop_key


class ShopKeyMiddleware:
    """Validate shop-key sources and store decoded context on the request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope)
            try:
                setattr(
                    request.state,
                    SHOP_CONTEXT_STATE_KEY,
                    parse_shop_key(request),
                )
            except AmbiguousShopKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=400)
                await response(scope, receive, send)
                return
            except InvalidShopKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=400)
                await response(scope, receive, send)
                return
            except MissingShopKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=401)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
