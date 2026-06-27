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


class ProductResponse(ObjectResponse):
    id = Normalizer.RAW
    name = Normalizer.DEFAULT_EMPTY
    default_code = Normalizer.OPTIONAL
    list_price = Normalizer.RAW
    uom_name = Normalizer.OPTIONAL
    barcode = Normalizer.OPTIONAL
    category = Normalizer.RAW
    available_qty = Normalizer.RAW
    qty_on_hand = Normalizer.RAW


_product_renderer = ProductResponse()

_PRODUCT_DISPLAY_FIELDS = [
    "id",
    "name",
    "list_price",
    "category",
    "available_qty",
    "qty_on_hand",
]

_PRODUCT_DETAIL_DISPLAY_FIELDS = [
    *_PRODUCT_DISPLAY_FIELDS,
    "default_code",
    "uom_name",
    "barcode",
]


def _product_agent_hint(*, item_count: int, search_term: str | None) -> dict[str, Any]:
    if item_count == 0:
        if search_term:
            return {"next": "ask_user_for_different_criteria"}
        return {}
    if item_count > 1 and search_term:
        return {
            "next": "disambiguate",
            "display": _PRODUCT_DISPLAY_FIELDS,
        }
    return {
        "next": "show_products",
        "display": _PRODUCT_DISPLAY_FIELDS,
    }


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
    raw_items = payload["items"]
    items = _product_renderer.render_many(raw_items)

    message: str | None = None
    if not items:
        if search_term:
            message = (
                "No hay productos que coincidan con la búsqueda. "
                "Prueba otro término o quita filtros."
            )
        elif category_id is not None:
            message = "No hay productos en esa categoría."

    result: dict[str, Any] = {
        "items": items,
        "limit": payload["limit"],
        "offset": payload["offset"],
        "total": payload["total"],
        "message": message,
    }
    agent_hint = _product_agent_hint(item_count=len(items), search_term=search_term)
    if agent_hint:
        result["_agent"] = agent_hint
    return result


async def get_product_detail(
    odoo: OdooJson2Client,
    *,
    product_id: int,
) -> dict[str, Any]:
    """Single product detail via ``product.product.api_get_product``."""
    raw = await odoo.call(
        "product.product",
        "api_get_product",
        product_id=product_id,
    )
    product = _product_renderer.render(raw)
    return {
        **product,
        "_agent": {"display": _PRODUCT_DETAIL_DISPLAY_FIELDS},
    }
