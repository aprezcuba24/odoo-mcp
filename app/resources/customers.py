"""Recurso de búsqueda de clientes Odoo."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services.customers import search_customers


async def read_customers(
    odoo: OdooJson2Client,
    *,
    query: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    return await search_customers(
        odoo,
        query=query,
        limit=limit,
    )


@mcp.resource(
    uri="app://customers",
    name="Clientes: listado",
    description=(
        "Lista clientes Odoo (res.partner con customer_rank > 0) sin filtros. "
        "limit acotado a 20."
    ),
    mime_type="application/json",
)
async def customers_list_resource(
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await read_customers(_odoo)


@mcp.resource(
    uri="app://customers{?query,limit}",
    name="Clientes: búsqueda",
    description=(
        "Busca clientes Odoo (res.partner con customer_rank > 0). "
        "query = texto libre que busca en nombre y teléfono (OR, ilike). "
        "limit acotado a 20."
    ),
    mime_type="application/json",
)
async def customers_resource(
    query: str | None = None,
    limit: int = 20,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await read_customers(
        _odoo,
        query=query,
        limit=limit,
    )
