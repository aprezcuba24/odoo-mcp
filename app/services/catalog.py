"""Catálogo de productos Odoo (product.product / product.category) vía JSON-2."""

from __future__ import annotations

from typing import Any

from app.clients.odoo_json2 import OdooJson2Client
from app.utils.object_response import ListResponse, Normalizer, ObjectResponse

DEFAULT_LIMIT = 80
MAX_LIMIT = 200


class CategoryResponse(ObjectResponse):
    id = Normalizer.RAW
    name = Normalizer.DEFAULT_EMPTY


async def list_categories(odoo: OdooJson2Client) -> dict[str, Any]:
    """Categories that have at least one visible catalog product."""
    rows = await odoo.call(
        "product.category",
        "search_read",
        fields=["name", "parent_id"],
        order="complete_name, id",
    )
    items = ListResponse(CategoryResponse(), items_key="categories").build(rows)
    return items


async def list_products_page(
    odoo: OdooJson2Client,
    *,
    limit: int | None = None,
    offset: int | None = None,
    category_id: int | None = None,
    search: str | None = None,
) -> dict[str, Any]:
    """Paginated product list via ``product.product.api_search_products``."""
    page_limit = min(limit if limit is not None else DEFAULT_LIMIT, MAX_LIMIT)
    page_offset = offset if offset is not None else 0
    search_term = str(search).strip() if search is not None and str(search).strip() else None

    params: dict[str, Any] = {
        "limit": page_limit,
        "offset": page_offset,
    }
    if search_term:
        params["query"] = search_term
    if category_id is not None:
        params["category_id"] = category_id

    payload = await odoo.call("product.product", "api_search_products", **params)
    items = payload["items"]

    message: str | None = None
    if not items:
        if search_term:
            message = (
                "No hay productos que coincidan con la búsqueda. "
                "Prueba otro término o quita filtros."
            )
        elif category_id is not None:
            message = "No hay productos en esa categoría."

    return {
        "items": items,
        "limit": payload["limit"],
        "offset": payload["offset"],
        "total": payload["total"],
        "message": message,
    }


async def get_product_detail(
    odoo: OdooJson2Client,
    *,
    product_id: int,
) -> dict[str, Any]:
    """Single product detail via ``product.product.api_get_product``."""
    return await odoo.call(
        "product.product",
        "api_get_product",
        product_id=product_id,
    )
