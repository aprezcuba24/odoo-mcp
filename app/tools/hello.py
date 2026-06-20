"""Tool de acción hola mundo — saludo personalizado."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.server import AuthenticatedAdminRef, get_authenticated_admin_api, mcp
from app.services.hello import build_hello_payload
from app.utils.shop_key_codec import resolve_shop_context


@mcp.tool(
    name="say_hello",
    description=(
        "Saluda al usuario por nombre. Devuelve mensaje personalizado y backend "
        "del shop-key. Usar después de leer admin://hello/message."
    ),
)
async def say_hello_tool(
    name: str,
    _auth: AuthenticatedAdminRef = Depends(get_authenticated_admin_api),
) -> dict[str, Any]:
    ctx = resolve_shop_context()
    return build_hello_payload(ctx, name=name)
