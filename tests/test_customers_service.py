"""Unit tests for customer search service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from app.services.customers import (
    CustomerSearchDomain,
    PartnerResponse,
    search_customers,
)

CUSTOMER_BASE_FILTERS = CustomerSearchDomain.base_filters
PARTNER_FIELDS = ["id", "name", "phone"]


def _query_domain(value: str) -> list:
    return [
        "|",
        ["name", "ilike", value],
        ["phone", "ilike", value],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_modes() -> None:
    assert CustomerSearchDomain().build_domain() == CUSTOMER_BASE_FILTERS
    assert CustomerSearchDomain(name="Acme").build_domain() == [
        ["name", "ilike", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(phone="555").build_domain() == [
        ["phone", "ilike", "555"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(name="Acme", phone="Acme").build_domain() == [
        "|",
        ["name", "ilike", "Acme"],
        ["phone", "ilike", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_normalize_partner_false_to_none() -> None:
    normalized = PartnerResponse().render(
        {
            "id": 1,
            "name": "Acme",
            "phone": False,
        }
    )
    assert normalized == {
        "id": 1,
        "name": "Acme",
        "phone": None,
    }


def test_search_customers_without_criteria() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {"id": 1, "name": "Acme", "phone": False},
            {"id": 2, "name": "Beta", "phone": False},
        ]
        result = await search_customers(odoo)
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=CUSTOMER_BASE_FILTERS,
            fields=PARTNER_FIELDS,
            limit=20,
        )
        assert result["count"] == 2
        assert result["message"] is None

    asyncio.run(run())


def test_search_customers_with_query_or_domain() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        await search_customers(odoo, query="Acme")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=_query_domain("Acme"),
            fields=PARTNER_FIELDS,
            limit=20,
        )

    asyncio.run(run())


def test_search_customers_with_query_multiple_results() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {"id": 1, "name": "Acme", "phone": False},
            {"id": 2, "name": "Acme", "phone": False},
        ]
        result = await search_customers(odoo, query="Acme")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=_query_domain("Acme"),
            fields=PARTNER_FIELDS,
            limit=20,
        )
        assert result["count"] == 2

    asyncio.run(run())


def test_search_customers_no_results_message() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await search_customers(odoo, query="missing@example.com")
        assert result["count"] == 0
        assert result["message"] is not None
        assert "no hay clientes" in result["message"].lower()

    asyncio.run(run())


def test_search_customers_no_results_without_criteria() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await search_customers(odoo)
        assert result["count"] == 0
        assert result["message"] == "No hay contactos registrados."

    asyncio.run(run())
