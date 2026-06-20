"""FastMCP server package."""

from __future__ import annotations

from .app_state import (
    AdminClientRef,
    AuthenticatedAdminRef,
    get_admin_api,
    get_authenticated_admin_api,
)
from app.utils.exceptions import AmbiguousShopKeyError, InvalidShopKeyError
from app.utils.shop_key_codec import (
    SHOP_KEY_HEADER,
    SHOP_KEY_QUERY_PARAM,
    ShopContext,
    resolve_shop_context,
    resolve_shop_key,
)
from .server import mcp, run

import app.tools  # noqa: F401  # register tools
import app.resources  # noqa: F401  # register resources
import app.prompts  # noqa: F401  # register prompts

__all__ = [
    "AdminClientRef",
    "AmbiguousShopKeyError",
    "AuthenticatedAdminRef",
    "InvalidShopKeyError",
    "SHOP_KEY_HEADER",
    "SHOP_KEY_QUERY_PARAM",
    "ShopContext",
    "get_admin_api",
    "get_authenticated_admin_api",
    "resolve_shop_context",
    "resolve_shop_key",
    "mcp",
    "run",
]
