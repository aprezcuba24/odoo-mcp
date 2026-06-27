"""Unit tests for cart MCP tools."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

from app.services.cart.memory import InMemoryCartStore
from app.utils.app_key_codec import app_context_from_encoded, encode_app_key

_CTX = app_context_from_encoded(
    encode_app_key("http://localhost:8069", "test-admin-key"),
)
_CART_KEY = _CTX.cart_store_key()


def test_cart_tools_flow() -> None:
    from app.tools import cart as cart_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(return_value=[{"name": "Deco Addict"}])

        with (
            patch("app.tools.cart.resolve_app_context", return_value=_CTX),
            patch("app.services.cart_session.cart_store", store),
        ):
            created = await cart_tools.create_cart_tool(partner_id=42, _odoo=odoo)
            assert created["partner_id"] == 42
            assert created["partner_name"] == "Deco Addict"
            assert created["line_count"] == 0

            added = await cart_tools.add_to_cart_tool(product_id=5, quantity=2.0)
            assert added["line_count"] == 1
            assert added["_agent"]["lines"] == [{"product_id": 5, "qty": 2.0}]
            assert added["_agent"]["next"] == "show_to_user_before_create_order"

            fetched = await cart_tools.get_cart_tool()
            assert fetched["partner_id"] == 42
            assert fetched["line_count"] == 1
            assert fetched["_agent"]["next"] == "show_to_user_before_create_order"

            cleared = await cart_tools.clear_cart_tool()
            assert cleared["partner_id"] is None
            assert cleared["message"] == "Carrito vaciado."

            empty = await cart_tools.get_cart_tool()
            assert empty["line_count"] == 0

    asyncio.run(run())


def test_add_to_cart_lines_json() -> None:
    from app.tools import cart as cart_tools

    async def run() -> None:
        store = InMemoryCartStore()
        odoo = AsyncMock()
        odoo.call = AsyncMock(return_value=[{"name": "Cliente"}])

        with (
            patch("app.tools.cart.resolve_app_context", return_value=_CTX),
            patch("app.services.cart_session.cart_store", store),
        ):
            await cart_tools.create_cart_tool(partner_id=1, _odoo=odoo)
            result = await cart_tools.add_to_cart_tool(
                lines_json='[{"product_id": 7, "qty": 2}, {"product_id": 12, "qty": 1}]',
            )
            assert result["line_count"] == 2
            assert result["_agent"]["lines"] == [
                {"product_id": 7, "qty": 2.0},
                {"product_id": 12, "qty": 1.0},
            ]
            assert result["_agent"]["next"] == "show_to_user_before_create_order"

    asyncio.run(run())
