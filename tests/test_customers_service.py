"""Unit tests for customer search service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from app.services.customers import PartnerResponse, search_customers

SAMPLE_PARTNER = {
    "id": 42,
    "name": "María",
    "phone": "+34600000000",
    "order_bridge_registered": True,
    "order_bridge_phone_validated": False,
    "address": {
        "street": "Calle 10",
        "municipality_id": 3,
        "municipality_name": "Camagüey",
        "neighborhood_id": 15,
        "neighborhood_name": "Centro",
        "state": "Camagüey",
    },
}


def test_normalize_partner_full_response() -> None:
    normalized = PartnerResponse().render(SAMPLE_PARTNER)
    assert normalized == SAMPLE_PARTNER


def test_normalize_partner_false_phone_to_none() -> None:
    normalized = PartnerResponse().render(
        {
            "id": 1,
            "name": "Acme",
            "phone": False,
            "order_bridge_registered": False,
            "order_bridge_phone_validated": False,
            "address": {},
        }
    )
    assert normalized == {
        "id": 1,
        "name": "Acme",
        "phone": None,
        "order_bridge_registered": False,
        "order_bridge_phone_validated": False,
        "address": {},
    }


def test_search_customers_without_criteria() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {**SAMPLE_PARTNER, "id": 1, "name": "Acme", "phone": False},
            {**SAMPLE_PARTNER, "id": 2, "name": "Beta", "phone": False},
        ]
        result = await search_customers(odoo)
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "api_search_customers",
            limit=20,
        )
        assert result["count"] == 2
        assert result["message"] is None
        assert result["customers"][0]["phone"] is None
        assert result["_agent"] == {"next": "disambiguate", "display": ["id", "name", "phone", "address"]}

    asyncio.run(run())


def test_search_customers_single_result_agent_hint() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [SAMPLE_PARTNER]
        result = await search_customers(odoo, query="María")
        assert result["count"] == 1
        assert result["_agent"] == {"next": "confirm_or_proceed"}

    asyncio.run(run())


def test_search_customers_with_query() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        await search_customers(odoo, query="Acme")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "api_search_customers",
            limit=20,
            query="Acme",
        )

    asyncio.run(run())


def test_search_customers_with_query_multiple_results() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {**SAMPLE_PARTNER, "id": 1, "name": "Acme"},
            {**SAMPLE_PARTNER, "id": 2, "name": "Acme"},
        ]
        result = await search_customers(odoo, query="Acme")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "api_search_customers",
            limit=20,
            query="Acme",
        )
        assert result["count"] == 2
        assert result["customers"][0]["address"]["neighborhood_name"] == "Centro"
        assert result["_agent"] == {"next": "disambiguate", "display": ["id", "name", "phone", "address"]}

    asyncio.run(run())


def test_search_customers_strips_query() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        await search_customers(odoo, query="  Acme  ")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "api_search_customers",
            limit=20,
            query="Acme",
        )

    asyncio.run(run())


def test_search_customers_no_results_message() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await search_customers(odoo, query="missing@example.com")
        assert result["count"] == 0
        assert result["message"] is not None
        assert "no hay clientes" in result["message"].lower()
        assert result["_agent"] == {"next": "ask_user_for_different_criteria"}

    asyncio.run(run())


def test_search_customers_no_results_without_criteria() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await search_customers(odoo)
        assert result["count"] == 0
        assert result["message"] == "No hay contactos registrados."
        assert result["_agent"] == {"next": "ask_user_for_different_criteria"}

    asyncio.run(run())
