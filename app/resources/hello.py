"""Recurso hola mundo — mensaje de bienvenida."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.server import get_odoo_client, mcp
from app.clients.odoo_json2 import OdooJson2Client
from app.services.hello import build_hello_payload
from app.utils.app_key_codec import resolve_app_context


async def read_hello_message(*, name: str | None = None) -> dict[str, Any]:
    ctx = resolve_app_context()
    return build_hello_payload(ctx, name=name)


@mcp.resource(
    uri="app://hello/message{?name}",
    name="Hola mundo: mensaje",
    description=(
        "Mensaje de bienvenida hola mundo. Parámetro opcional name personaliza el saludo. "
        "Incluye backend (URL del auth-key) para verificar autenticación."
    ),
    mime_type="application/json",
)
async def hello_message_resource(
    name: str | None = None,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await read_hello_message(name=name)
