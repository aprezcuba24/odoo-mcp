"""Tool de lectura hola mundo — equivalente a Resource app://hello/message."""

from __future__ import annotations

from typing import Any

from app.resources.hello import read_hello_message
from app.server import mcp
from app.tools.tool_resources._common import READ_ONLY


@mcp.tool(
    name="read_hello_message",
    description=(
        "Mensaje de bienvenida hola mundo. Parámetro opcional name personaliza el saludo. "
        "Equivalente al Resource app://hello/message."
    ),
    annotations=READ_ONLY,
)
async def read_hello_message_tool(name: str | None = None) -> dict[str, Any]:
    return await read_hello_message(name=name)
