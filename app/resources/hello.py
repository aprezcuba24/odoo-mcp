"""Recurso hola mundo — mensaje de bienvenida."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.server import AdminClientRef, get_admin_api, mcp
from app.services.hello import build_hello_payload
from app.utils.shop_key_codec import resolve_shop_context


async def read_hello_message(*, name: str | None = None) -> dict[str, Any]:
    ctx = resolve_shop_context()
    return build_hello_payload(ctx, name=name)


@mcp.resource(
    uri="admin://hello/message{?name}",
    name="Hola mundo: mensaje",
    description=(
        "Mensaje de bienvenida hola mundo. Parámetro opcional name personaliza el saludo. "
        "Incluye backend (URL del shop-key) para verificar autenticación."
    ),
    mime_type="application/json",
)
async def hello_message_resource(
    name: str | None = None,
    _api: AdminClientRef = Depends(get_admin_api),
) -> dict[str, Any]:
    return await read_hello_message(name=name)
