"""Unit tests for customer search service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

from app.services.customers import (
    FIELDS,
    _build_domain,
    _effective_limit,
    _normalize_partner,
    _resolve_search_mode,
    search_customers,
)


def test_resolve_search_mode_priority() -> None:
    assert _resolve_search_mode(query="a", name="b", vat="c", email="d") == ("name", "b")
    assert _resolve_search_mode(query="a", name=None, vat="c", email="d") == ("vat", "c")
    assert _resolve_search_mode(query="a", name=None, vat=None, email="d") == ("email", "d")
    assert _resolve_search_mode(query="a", name=None, vat=None, email=None) == ("query", "a")
    assert _resolve_search_mode(query=None, name=None, vat=None, email=None) is None


def test_build_domain_modes() -> None:
    assert _build_domain("query", "Deco") == [
        ["name", "ilike", "Deco"],
        ["customer_rank", ">", 0],
    ]
    assert _build_domain("name", "Acme") == [
        ["name", "=", "Acme"],
        ["customer_rank", ">", 0],
    ]
    assert _build_domain("vat", "ES123") == [
        ["vat", "ilike", "ES123"],
        ["customer_rank", ">", 0],
    ]
    assert _build_domain("email", "a@b.com") == [
        ["email", "ilike", "a@b.com"],
        ["customer_rank", ">", 0],
    ]


def test_effective_limit() -> None:
    assert _effective_limit("name", 20) == 2
    assert _effective_limit("query", 50) == 20
    assert _effective_limit("query", 5) == 5


def test_normalize_partner_false_to_none() -> None:
    normalized = _normalize_partner(
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
        result = await search_customers(odoo)
        assert result["count"] == 0
        assert result["customers"] == []
        assert result["search"] is None
        assert "criterio" in (result["message"] or "").lower()
        odoo.call.assert_not_called()

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
            domain=[["name", "ilike", "Deco"], ["customer_rank", ">", 0]],
            fields=FIELDS,
            limit=5,
        )
        assert result["count"] == 1
        assert result["ambiguous"] is False
        assert result["customers"][0]["name"] == "Deco Addict"

    asyncio.run(run())


def test_search_customers_exact_name_ambiguous() -> None:
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
            domain=[["name", "=", "Acme"], ["customer_rank", ">", 0]],
            fields=FIELDS,
            limit=2,
        )
        assert result["count"] == 2
        assert result["ambiguous"] is True
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
