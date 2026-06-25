"""Tools de lectura de catálogo — equivalente a Resources app://catalog/..."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.services.catalog import (
    get_product_detail,
    list_categories,
    list_products_page,
)
from app.server import get_odoo_client, mcp
from app.tools.tool_resources._common import READ_ONLY


@mcp.tool(
    name="read_catalog_categories",
    description=(
        "Lista categorías de producto del catálogo admin "
        "(product.category search_read vía JSON-2). "
        "Equivalente al Resource app://catalog/categories."
    ),
    annotations=READ_ONLY,
)
async def read_catalog_categories_tool(
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await list_categories(_odoo)


@mcp.tool(
    name="read_catalog_products",
    description=(
        "Lista productos del catálogo (product.product api_search_products vía JSON-2). "
        "Admite búsqueda por nombre (search), filtro por categoría (category_id) y paginación "
        "(limit, offset). Equivalente al Resource app://catalog/products."
    ),
    annotations=READ_ONLY,
)
async def read_catalog_products_tool(
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


@mcp.tool(
    name="read_catalog_product",
    description=(
        "Detalle de un producto por ID (product.product api_get_product vía JSON-2): "
        "nombre, precio, categoría, código, unidad de medida y código de barras. "
        "Equivalente al Resource app://catalog/products/{product_id}."
    ),
    annotations=READ_ONLY,
)
async def read_catalog_product_tool(
    product_id: int,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    return await get_product_detail(_odoo, product_id=product_id)
