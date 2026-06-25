"""Recursos de catálogo — categorías y productos Odoo."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services.catalog import (
    get_product_detail,
    list_categories,
    list_products_page,
)


@mcp.resource(
    uri="app://catalog/categories",
    name="Catálogo: categorías",
    description=(
        "Lista categorías de producto con al menos un producto visible en el catálogo "
        "(product.category search_read vía JSON-2)."
    ),
    mime_type="application/json",
)
async def categories_resource(
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await list_categories(_odoo)


@mcp.resource(
    uri="app://catalog/products",
    name="Catálogo: productos (listado)",
    description=(
        "Listado de productos del catálogo sin filtros (público admin). "
        "Para búsqueda o paginación usar el template con parámetros."
    ),
    mime_type="application/json",
)
async def products_list_resource(
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await list_products_page(_odoo)


@mcp.resource(
    uri="app://catalog/products{?limit,offset,category_id,search}",
    name="Catálogo: productos",
    description=(
        "Lista productos del catálogo (product.product api_search_products). "
        "search = nombre parcial; category_id = filtro por categoría; limit/offset paginación."
    ),
    mime_type="application/json",
)
async def products_resource(
    limit: int | None = None,
    offset: int | None = None,
    category_id: int | None = None,
    search: str | None = None,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await list_products_page(
        _odoo,
        limit=limit,
        offset=offset,
        category_id=category_id,
        search=search,
    )


@mcp.resource(
    uri="app://catalog/products/{product_id}",
    name="Detalle de producto",
    description=(
        "Detalle de un producto por ID: nombre, precio, categoría, código, "
        "unidad de medida y código de barras."
    ),
    mime_type="application/json",
)
async def product_resource(
    product_id: int,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await get_product_detail(_odoo, product_id=product_id)
