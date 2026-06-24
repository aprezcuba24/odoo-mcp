"""Unit tests for orders service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from app.services.orders import create_confirmed_order


def test_create_confirmed_order_calls_odoo() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call = AsyncMock(
            return_value={
                "id": 15,
                "name": "S00015",
                "state": "sale",
                "amount_total": 20.0,
                "partner_id": 42,
                "client_order_ref": "PO-123",
            }
        )

        result = await create_confirmed_order(
            odoo,
            partner_id=42,
            lines=[{"product_id": 7, "qty": 2}, {"product_id": 12, "qty": 1}],
            ref="PO-123",
        )

        odoo.call.assert_awaited_once_with(
            "sale.order",
            "api_create_confirmed_order",
            partner_id=42,
            lines=[{"product_id": 7, "qty": 2}, {"product_id": 12, "qty": 1}],
            ref="PO-123",
        )
        assert result["id"] == 15
        assert result["name"] == "S00015"
        assert result["state"] == "sale"
        assert result["amount_total"] == 20.0
        assert result["partner_id"] == 42
        assert result["client_order_ref"] == "PO-123"
        assert result["_agent"]["order_id"] == 15

    asyncio.run(run())


def test_create_confirmed_order_omits_empty_ref() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call = AsyncMock(return_value={"id": 1, "name": "S00001", "state": "sale"})

        await create_confirmed_order(
            odoo,
            partner_id=1,
            lines=[{"product_id": 1, "qty": 1.0}],
            ref="   ",
        )

        odoo.call.assert_awaited_once_with(
            "sale.order",
            "api_create_confirmed_order",
            partner_id=1,
            lines=[{"product_id": 1, "qty": 1.0}],
        )

    asyncio.run(run())
