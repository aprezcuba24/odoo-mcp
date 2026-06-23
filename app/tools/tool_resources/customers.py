"""Tool de lectura de clientes — equivalente a Resource app://customers."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services.customers import search_customers
from app.tools.tool_resources._common import READ_ONLY


@mcp.tool(
    name="read_customers",
    description=(
        "Busca clientes Odoo (res.partner con customer_rank > 0). "
        "Criterios: query (nombre parcial), name (exacto), vat (NIF/CIF), email. "
        "Equivalente al Resource app://customers."
    ),
    annotations=READ_ONLY,
)
async def read_customers_tool(
    query: str | None = None,
    name: str | None = None,
    vat: str | None = None,
    email: str | None = None,
    limit: int = 20,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await search_customers(
        _odoo,
        query=query,
        name=name,
        vat=vat,
        email=email,
        limit=limit,
    )
