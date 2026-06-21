"""Tool de acción hola mundo — saludo personalizado."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.server import get_odoo_client, mcp
from app.clients.odoo_json2 import OdooJson2Client
from app.services.hello import build_hello_payload
from app.utils.app_key_codec import resolve_app_context


@mcp.tool(
    name="say_hello",
    description=(
        "Saluda al usuario por nombre. Devuelve mensaje personalizado y backend "
        "del auth-key. Usar después de leer app://hello/message."
    ),
)
async def say_hello_tool(
    name: str,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    ctx = resolve_app_context()
    return build_hello_payload(ctx, name=name)
