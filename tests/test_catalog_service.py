"""Unit tests for catalog service."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.services.catalog import get_product_detail, list_categories, list_products_page
from app.utils.exceptions import ValidationApiError

SAMPLE_PRODUCT = {
    "id": 7,
    "name": "Agua mineral",
    "default_code": "AGUA-01",
    "list_price": 0.8,
    "uom_name": "Units",
    "barcode": False,
    "category": {
        "id": 3,
        "name": "Bebidas",
        "parent_id": 1,
    },
}


def test_list_categories_empty() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = []
        result = await list_categories(odoo)
        odoo.call.assert_awaited_once_with(
            "product.category",
            "search_read",
            fields=["name", "parent_id"],
            order="complete_name, id",
        )
        assert result["count"] == 0
        assert result["categories"] == []
        assert result["message"] is None

    asyncio.run(run())


def test_list_categories_with_rows() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = [
            {
                "id": 3,
                "name": "Lácteos",
                "parent_id": [1, "Alimentos"],
            }
        ]
        result = await list_categories(odoo)
        assert result["count"] == 1
        assert result["categories"] == [
            {"id": 3, "name": "Lácteos"},
        ]

    asyncio.run(run())


def test_list_products_page_api_call() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = {
            "items": [],
            "limit": 10,
            "offset": 5,
            "total": 0,
        }
        await list_products_page(
            odoo,
            limit=10,
            offset=5,
            category_id=3,
            search="arroz",
        )
        odoo.call.assert_awaited_once_with(
            "product.product",
            "api_search_products",
            limit=10,
            offset=5,
            query="arroz",
            category_id=3,
        )

    asyncio.run(run())


def test_list_products_page_passthrough() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = {
            "items": [SAMPLE_PRODUCT],
            "limit": 80,
            "offset": 0,
            "total": 1,
        }
        result = await list_products_page(odoo)
        assert result["total"] == 1
        assert result["limit"] == 80
        assert result["offset"] == 0
        assert result["items"][0] == SAMPLE_PRODUCT
        assert result["message"] is None

    asyncio.run(run())


def test_list_products_page_no_results_message() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = {
            "items": [],
            "limit": 80,
            "offset": 0,
            "total": 0,
        }
        result = await list_products_page(odoo, search="missing")
        assert result["items"] == []
        assert result["message"] is not None
        assert "búsqueda" in result["message"].lower()

    asyncio.run(run())


def test_get_product_detail_validation_error() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.side_effect = ValidationApiError(
            "El producto 7 no está disponible.",
            status_code=422,
            body={"message": "El producto 7 no está disponible."},
        )
        with pytest.raises(ValidationApiError, match="no está disponible"):
            await get_product_detail(odoo, product_id=7)
        odoo.call.assert_awaited_once_with(
            "product.product",
            "api_get_product",
            product_id=7,
        )

    asyncio.run(run())


def test_get_product_detail_success() -> None:
    async def run() -> None:
        odoo = AsyncMock()
        odoo.call.return_value = SAMPLE_PRODUCT
        result = await get_product_detail(odoo, product_id=7)
        odoo.call.assert_awaited_once_with(
            "product.product",
            "api_get_product",
            product_id=7,
        )
        assert result == SAMPLE_PRODUCT

    asyncio.run(run())
