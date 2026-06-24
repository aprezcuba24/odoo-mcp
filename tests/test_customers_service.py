"""Unit tests for customer search service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from app.services.customers import (
    FIELDS,
    CustomerSearchDomain,
    PartnerResponse,
    search_customers,
)


def test_resolve_search_mode_priority() -> None:
    assert CustomerSearchDomain(query="a", name="b", vat="c", email="d").resolve_criterion() == ("name", "b")
    assert CustomerSearchDomain(query="a", name=None, vat="c", email="d").resolve_criterion() == ("vat", "c")
    assert CustomerSearchDomain(query="a", name=None, vat=None, email="d").resolve_criterion() == ("email", "d")
    assert CustomerSearchDomain(query="a", name=None, vat=None, email=None).resolve_criterion() == ("query", "a")
    assert CustomerSearchDomain(query=None, name=None, vat=None, email=None).resolve_criterion() is None


def test_build_domain_modes() -> None:
    assert CustomerSearchDomain(query="Deco").build_domain() == [["name", "ilike", "Deco"]]
    assert CustomerSearchDomain(name="Acme").build_domain() == [["name", "=", "Acme"]]
    assert CustomerSearchDomain(vat="ES123").build_domain() == [["vat", "ilike", "ES123"]]
    assert CustomerSearchDomain(email="a@b.com").build_domain() == [["email", "ilike", "a@b.com"]]


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
            domain=[],
            fields=FIELDS,
            limit=20,
        )
        assert result["count"] == 2
        assert result["search"] is None
        assert result["message"] is None

    asyncio.run(run())


def test_search_customers_query_calls_odoo() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {"id": 1, "name": "Deco Addict", "email": "a@b.com", "phone": "123", "vat": "ES1"},
        ]
        result = await search_customers(odoo, query="Deco", limit=5)
        odoo.call.assert_awaited_once_with(
            "res.partner",
            "search_read",
            domain=[["name", "ilike", "Deco"]],
            fields=FIELDS,
            limit=5,
        )
        assert result["count"] == 1
        assert result["customers"][0]["name"] == "Deco Addict"

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
            domain=[["name", "=", "Acme"]],
            fields=FIELDS,
            limit=20,
        )
        assert result["count"] == 2
        assert result["search"] == {"mode": "name", "value": "Acme"}

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
