"""FastMCP server package."""

from __future__ import annotations

from .app_state import (
    AppClientRef,
    AuthenticatedAppRef,
    get_app_api,
    get_authenticated_app_api,
)
from app.utils.exceptions import AmbiguousAuthKeyError, InvalidAuthKeyError
from app.utils.app_key_codec import (
    APP_KEY_HEADER,
    APP_KEY_QUERY_PARAM,
    AppContext,
    resolve_app_context,
    resolve_app_key,
)
from .server import mcp, run

import app.tools  # noqa: F401  # register tools
import app.resources  # noqa: F401  # register resources
import app.prompts  # noqa: F401  # register prompts

__all__ = [
    "AppClientRef",
    "AmbiguousAuthKeyError",
    "AuthenticatedAppRef",
    "InvalidAuthKeyError",
    "APP_KEY_HEADER",
    "APP_KEY_QUERY_PARAM",
    "AppContext",
    "get_app_api",
    "get_authenticated_app_api",
    "resolve_app_context",
    "resolve_app_key",
    "mcp",
    "run",
]
