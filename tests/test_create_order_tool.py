"""Unit tests for create_order tool."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.cart.memory import InMemoryCartStore
from app.utils.app_key_codec import app_context_from_encoded, encode_app_key

_CTX = app_context_from_encoded(
    encode_app_key("http://localhost:8069", "test-admin-key"),
)
_CART_KEY = _CTX.cart_store_key()


def test_create_order_no_customer() -> None:
    from app.tools import orders as orders_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()

        with (
            patch("app.tools.orders.resolve_app_context", return_value=_CTX),
            patch("app.tools.orders.cart_store", store),
        ):
            result = await orders_tools.create_order_tool(_odoo=odoo)

        assert result["ok"] is False
        assert result["error"] == "no_customer"
        odoo.call.assert_not_called()

    asyncio.run(run())


def test_create_order_empty_cart() -> None:
    from app.tools import orders as orders_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()

        with (
            patch("app.tools.orders.resolve_app_context", return_value=_CTX),
            patch("app.tools.orders.cart_store", store),
        ):
            await store.set_partner(_CART_KEY, partner_id=42, partner_name="Deco")
            result = await orders_tools.create_order_tool(_odoo=odoo)

        assert result["ok"] is False
        assert result["error"] == "empty_cart"
        odoo.call.assert_not_called()

    asyncio.run(run())


def test_create_order_success_clears_cart() -> None:
    from app.tools import orders as orders_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(
            return_value={
                "id": 101,
                "name": "S00101",
                "state": "sale",
                "amount_total": 50.0,
                "partner_id": 42,
                "client_order_ref": False,
            }
        )

        with (
            patch("app.tools.orders.resolve_app_context", return_value=_CTX),
            patch("app.tools.orders.cart_store", store),
            patch(
                "app.tools.orders.create_confirmed_order",
                new_callable=AsyncMock,
                return_value={
                    "id": 101,
                    "name": "S00101",
                    "state": "sale",
                    "amount_total": 50.0,
                    "partner_id": 42,
                    "client_order_ref": False,
                    "_agent": {"order_id": 101},
                },
            ) as mock_create,
        ):
            await store.set_partner(_CART_KEY, partner_id=42, partner_name="Deco")
            await store.add_lines(_CART_KEY, [(5, 2.0)])

            result = await orders_tools.create_order_tool(ref="PO-99", _odoo=odoo)

        assert result["ok"] is True
        assert result["order"]["name"] == "S00101"
        assert result["cart_cleared"] is True
        mock_create.assert_awaited_once()
        cart = await store.get_cart(_CART_KEY)
        assert cart.partner_id is None
        assert cart.lines == []

    asyncio.run(run())


def test_create_order_failure_keeps_cart() -> None:
    from app.tools import orders as orders_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()

        with (
            patch("app.tools.orders.resolve_app_context", return_value=_CTX),
            patch("app.tools.orders.cart_store", store),
            patch(
                "app.tools.orders.create_confirmed_order",
                new_callable=AsyncMock,
                side_effect=RuntimeError("Odoo error"),
            ),
        ):
            await store.set_partner(_CART_KEY, partner_id=42, partner_name="Deco")
            await store.add_lines(_CART_KEY, [(5, 2.0)])

            try:
                await orders_tools.create_order_tool(_odoo=odoo)
            except RuntimeError:
                pass

            cart = await store.get_cart(_CART_KEY)
            assert cart.partner_id == 42
            assert len(cart.lines) == 1
            assert cart.lines[0].qty == 2.0

    asyncio.run(run())
