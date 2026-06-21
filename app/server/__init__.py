"""FastMCP server package."""

from __future__ import annotations

from .app_state import get_odoo_client
from app.clients.odoo_json2 import OdooJson2Client
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
    "AmbiguousAuthKeyError",
    "InvalidAuthKeyError",
    "OdooJson2Client",
    "APP_KEY_HEADER",
    "APP_KEY_QUERY_PARAM",
    "AppContext",
    "get_odoo_client",
    "resolve_app_context",
    "resolve_app_key",
    "mcp",
    "run",
]
