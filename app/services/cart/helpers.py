"""Helpers for cart line serialization and tool responses."""

from __future__ import annotations

from typing import Any

from app.services.cart.base import AdminCart, CartLine


def lines_payload(lines: list[CartLine]) -> list[dict[str, float | int]]:
    return [{"product_id": line.product_id, "qty": line.qty} for line in lines]


def enriched_lines_payload(
    lines: list[CartLine],
    products_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for line in lines:
        item: dict[str, Any] = {"product_id": line.product_id, "qty": line.qty}
        product = products_by_id.get(line.product_id)
        if product:
            list_price = float(product.get("list_price") or 0)
            item["name"] = product.get("name", "")
            item["list_price"] = list_price
            item["subtotal"] = list_price * line.qty
            if product.get("available_qty") is not None:
                item["available_qty"] = product["available_qty"]
            if product.get("qty_on_hand") is not None:
                item["qty_on_hand"] = product["qty_on_hand"]
        result.append(item)
    return result


def cart_response(
    cart: AdminCart,
    *,
    products_by_id: dict[int, dict[str, Any]] | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    line_count, total_qty = (
        (0, 0.0)
        if not cart.lines
        else (len(cart.lines), sum(line.qty for line in cart.lines))
    )
    if cart.lines and products_by_id is not None:
        lines = enriched_lines_payload(cart.lines, products_by_id)
        amount_total = sum(line.get("subtotal", 0.0) for line in lines)
    else:
        lines = lines_payload(cart.lines)
        amount_total = None

    payload: dict[str, Any] = {
        "partner_id": cart.partner_id,
        "partner_name": cart.partner_name,
        "line_count": line_count,
        "total_qty": total_qty,
        "lines": lines,
        "_agent": {
            "partner_id": cart.partner_id,
            "lines": lines,
        },
    }
    if amount_total is not None:
        payload["amount_total"] = amount_total
        payload["_agent"]["amount_total"] = amount_total
    if cart.lines:
        payload["_agent"]["next"] = "show_to_user_before_create_order"
    if message is not None:
        payload["message"] = message
    return payload
