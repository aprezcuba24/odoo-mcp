"""Helpers for cart line serialization and tool responses."""

from __future__ import annotations

from typing import Any

from app.services.cart.base import AdminCart, CartLine


def lines_payload(lines: list[CartLine]) -> list[dict[str, float | int]]:
    return [{"product_id": line.product_id, "qty": line.qty} for line in lines]


def cart_response(
    cart: AdminCart,
    *,
    message: str | None = None,
) -> dict[str, Any]:
    line_count, total_qty = (
        (0, 0.0)
        if not cart.lines
        else (len(cart.lines), sum(line.qty for line in cart.lines))
    )
    payload: dict[str, Any] = {
        "partner_id": cart.partner_id,
        "partner_name": cart.partner_name,
        "line_count": line_count,
        "total_qty": total_qty,
        "lines": lines_payload(cart.lines),
        "_agent": {
            "partner_id": cart.partner_id,
            "lines": lines_payload(cart.lines),
        },
    }
    if cart.lines:
        payload["_agent"]["next"] = "show_to_user_before_create_order"
    if message is not None:
        payload["message"] = message
    return payload
