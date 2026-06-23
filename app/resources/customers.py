"""Recurso de búsqueda de clientes Odoo."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services.customers import search_customers


@mcp.resource(
    uri="app://customers{?query,name,vat,email,limit}",
    name="Clientes: búsqueda",
    description=(
        "Busca clientes Odoo (res.partner con customer_rank > 0). "
        "Criterios mutuamente excluyentes (prioridad: name > vat > email > query): "
        "query = nombre parcial (ilike), name = nombre exacto, vat = NIF/CIF, email = correo. "
        "limit acotado a 20 (name exacto usa limit=2 para validar unicidad)."
    ),
    mime_type="application/json",
)
async def customers_resource(
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
