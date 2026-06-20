"""Resolve auth-key once per HTTP request and attach it to request state."""

from __future__ import annotations

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.utils.exceptions import (
    AmbiguousAuthKeyError,
    InvalidAuthKeyError,
    MissingAuthKeyError,
)
from app.utils.app_key_codec import APP_CONTEXT_STATE_KEY, parse_app_key


class AppKeyMiddleware:
    """Validate auth-key sources and store decoded context on the request."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            request = Request(scope)
            try:
                setattr(
                    request.state,
                    APP_CONTEXT_STATE_KEY,
                    parse_app_key(request),
                )
            except AmbiguousAuthKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=400)
                await response(scope, receive, send)
                return
            except InvalidAuthKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=400)
                await response(scope, receive, send)
                return
            except MissingAuthKeyError as exc:
                response = JSONResponse({"error": str(exc)}, status_code=401)
                await response(scope, receive, send)
                return

        await self.app(scope, receive, send)
