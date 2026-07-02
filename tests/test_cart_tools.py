"""Unit tests for cart MCP tools."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

from app.services.cart.memory import InMemoryCartStore
from app.utils.app_key_codec import app_context_from_encoded, encode_app_key
from app.utils.exceptions import ValidationApiError

_CTX = app_context_from_encoded(
    encode_app_key("http://localhost:8069", "test-admin-key"),
)

SAMPLE_PRODUCTS = [
    {
        "id": 5,
        "name": "Agua mineral",
        "list_price": 0.8,
        "available_qty": 12.0,
        "qty_on_hand": 15.0,
    },
    {
        "id": 7,
        "name": "Arroz",
        "list_price": 2.5,
        "available_qty": 20.0,
        "qty_on_hand": 25.0,
    },
    {
        "id": 12,
        "name": "Aceite",
        "list_price": 4.0,
        "available_qty": 8.0,
        "qty_on_hand": 10.0,
    },
]


def _odoo_call_side_effect(model: str, method: str, **kwargs: Any) -> Any:
    if model == "res.partner" and method == "read":
        return [{"name": "Deco Addict"}]
    if model == "product.product" and method == "api_get_product":
        product_id = kwargs.get("product_id")
        matches = [p for p in SAMPLE_PRODUCTS if p["id"] == product_id]
        if not matches:
            raise ValidationApiError("Producto no disponible.", status_code=422)
        return matches[0]
    raise AssertionError(f"Unexpected Odoo call: {model}.{method} {kwargs}")


def test_cart_tools_flow() -> None:
    from app.tools import cart as cart_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(side_effect=_odoo_call_side_effect)

        with (
            patch("app.tools.cart.resolve_app_context", return_value=_CTX),
            patch("app.services.cart_session.cart_store", store),
        ):
            created = await cart_tools.create_cart_tool(partner_id=42, _odoo=odoo)
            assert created["partner_id"] == 42
            assert created["partner_name"] == "Deco Addict"
            assert created["line_count"] == 0
            assert "amount_total" not in created

            added = await cart_tools.add_to_cart_tool(
                product_id=5, quantity=2.0, _odoo=odoo
            )
            assert added["line_count"] == 1
            assert added["lines"] == [
                {
                    "product_id": 5,
                    "qty": 2.0,
                    "name": "Agua mineral",
                    "list_price": 0.8,
                    "subtotal": 1.6,
                    "available_qty": 12.0,
                    "qty_on_hand": 15.0,
                }
            ]
            assert added["amount_total"] == 1.6
            assert added["_agent"]["next"] == "show_to_user_before_create_order"

            fetched = await cart_tools.get_cart_tool(_odoo=odoo)
            assert fetched["partner_id"] == 42
            assert fetched["line_count"] == 1
            assert fetched["amount_total"] == 1.6
            assert fetched["_agent"]["next"] == "show_to_user_before_create_order"

            cleared = await cart_tools.clear_cart_tool()
            assert cleared["partner_id"] is None
            assert cleared["message"] == "Carrito vaciado."

            empty = await cart_tools.get_cart_tool(_odoo=odoo)
            assert empty["line_count"] == 0
            assert "amount_total" not in empty

    asyncio.run(run())


def test_add_to_cart_lines_json() -> None:
    from app.tools import cart as cart_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(
            side_effect=lambda model, method, **kwargs: (
                [{"name": "Cliente"}]
                if model == "res.partner"
                else next(
                    p
                    for p in SAMPLE_PRODUCTS
                    if p["id"] == kwargs.get("product_id")
                )
            )
        )

        with (
            patch("app.tools.cart.resolve_app_context", return_value=_CTX),
            patch("app.services.cart_session.cart_store", store),
        ):
            await cart_tools.create_cart_tool(partner_id=1, _odoo=odoo)
            result = await cart_tools.add_to_cart_tool(
                lines_json='[{"product_id": 7, "qty": 2}, {"product_id": 12, "qty": 1}]',
                _odoo=odoo,
            )
            assert result["line_count"] == 2
            assert result["lines"][0]["name"] == "Arroz"
            assert result["lines"][0]["subtotal"] == 5.0
            assert result["lines"][1]["name"] == "Aceite"
            assert result["lines"][1]["subtotal"] == 4.0
            assert result["amount_total"] == 9.0
            assert result["_agent"]["next"] == "show_to_user_before_create_order"

    asyncio.run(run())


def _odoo_call_unknown_product_side_effect(model: str, method: str, **kwargs: Any) -> Any:
    if model == "res.partner" and method == "read":
        return [{"name": "Cliente"}]
    if model == "product.product" and method == "api_get_product":
        raise ValidationApiError("Producto no disponible.", status_code=422)
    raise AssertionError(f"Unexpected Odoo call: {model}.{method} {kwargs}")


def test_add_to_cart_unknown_product_keeps_basic_line() -> None:
    from app.tools import cart as cart_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(side_effect=_odoo_call_unknown_product_side_effect)

        with (
            patch("app.tools.cart.resolve_app_context", return_value=_CTX),
            patch("app.services.cart_session.cart_store", store),
        ):
            await cart_tools.create_cart_tool(partner_id=1, _odoo=odoo)
            result = await cart_tools.add_to_cart_tool(
                product_id=999, quantity=1.0, _odoo=odoo
            )
            assert result["lines"] == [{"product_id": 999, "qty": 1.0}]
            assert result["amount_total"] == 0.0

    asyncio.run(run())
