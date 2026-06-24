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
PARTNER_FIELDS = ["id", "name", "email", "phone", "vat"]


def test_build_domain_modes() -> None:
    assert CustomerSearchDomain().build_domain() == CUSTOMER_BASE_FILTERS
    assert CustomerSearchDomain(name="Acme").build_domain() == [
        ["name", "=", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(vat="ES123").build_domain() == [
        ["vat", "ilike", "ES123"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(email="a@b.com").build_domain() == [
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(name="Acme", email="a@b.com").build_domain() == [
        "|",
        ["name", "=", "Acme"],
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]
    assert CustomerSearchDomain(name="Acme", vat="ES", email="a@b.com").build_domain() == [
        "|",
        "|",
        ["name", "=", "Acme"],
        ["vat", "ilike", "ES"],
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_normalize_partner_false_to_none() -> None:
    normalized = PartnerResponse().render(
        {
            "id": 1,
            "name": "Acme",
            "email": False,
            "phone": False,
            "vat": "ES123",
        }
    )
    assert normalized == {
        "id": 1,
        "name": "Acme",
        "email": None,
        "phone": None,
        "vat": "ES123",
    }


def test_search_customers_without_criteria() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {"id": 1, "name": "Acme", "email": False, "phone": False, "vat": False},
            {"id": 2, "name": "Beta", "email": False, "phone": False, "vat": False},
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


def test_search_customers_multiple_criteria_or() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        await search_customers(odoo, name="Acme", email="x@y.com")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=[
                "|",
                ["name", "=", "Acme"],
                ["email", "ilike", "x@y.com"],
                *CUSTOMER_BASE_FILTERS,
            ],
            fields=PARTNER_FIELDS,
            limit=20,
        )

    asyncio.run(run())


def test_search_customers_exact_name_multiple_results() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {"id": 1, "name": "Acme", "email": False, "phone": False, "vat": False},
            {"id": 2, "name": "Acme", "email": False, "phone": False, "vat": False},
        ]
        result = await search_customers(odoo, name="Acme")
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=[["name", "=", "Acme"], *CUSTOMER_BASE_FILTERS],
            fields=PARTNER_FIELDS,
            limit=20,
        )
        assert result["count"] == 2

    asyncio.run(run())


def test_search_customers_no_results_message() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await search_customers(odoo, email="missing@example.com")
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
