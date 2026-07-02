"""Unit tests for cart response helpers."""

from __future__ import annotations

from app.services.cart.base import AdminCart, CartLine
from app.services.cart.helpers import cart_response, enriched_lines_payload


def test_enriched_lines_payload() -> None:
    lines = [CartLine(product_id=7, qty=2.0), CartLine(product_id=99, qty=1.0)]
    products = {
        7: {
            "id": 7,
            "name": "Arroz",
            "list_price": 2.5,
            "available_qty": 10.0,
            "qty_on_hand": 12.0,
        },
    }
    result = enriched_lines_payload(lines, products)
    assert result[0] == {
        "product_id": 7,
        "qty": 2.0,
        "name": "Arroz",
        "list_price": 2.5,
        "subtotal": 5.0,
        "available_qty": 10.0,
        "qty_on_hand": 12.0,
    }
    assert result[1] == {"product_id": 99, "qty": 1.0}


def test_cart_response_with_enrichment() -> None:
    cart = AdminCart(
        partner_id=1,
        partner_name="Cliente",
        lines=[CartLine(product_id=7, qty=2.0)],
    )
    products = {7: {"id": 7, "name": "Arroz", "list_price": 2.5}}
    payload = cart_response(cart, products_by_id=products)
    assert payload["amount_total"] == 5.0
    assert payload["_agent"]["amount_total"] == 5.0
    assert payload["_agent"]["next"] == "show_to_user_before_create_order"
