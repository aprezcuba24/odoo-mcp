"""Unit tests for in-memory admin cart store."""

from __future__ import annotations

import asyncio

import pytest

from app.services.cart.base import CartStoreKey
from app.services.cart.memory import InMemoryCartStore
from app.utils.app_key_codec import app_context_from_encoded, encode_app_key


def _cart_key(base_url: str, token: str) -> CartStoreKey:
    return app_context_from_encoded(encode_app_key(base_url, token)).cart_store_key()


_KEY_A = _cart_key("https://a.example.com", "token-a")
_KEY_B = _cart_key("https://b.example.com", "token-b")


def test_set_partner_starts_session() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        cart = await store.set_partner(_KEY_A, partner_id=42, partner_name="Deco")

        assert cart.partner_id == 42
        assert cart.partner_name == "Deco"
        assert cart.lines == []

    asyncio.run(run())


def test_set_partner_rejects_active_session() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        await store.set_partner(_KEY_A, partner_id=42, partner_name="Deco")

        with pytest.raises(ValueError, match="carrito activo"):
            await store.set_partner(_KEY_A, partner_id=99, partner_name="Otro")

    asyncio.run(run())


def test_add_lines_accumulates_qty() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        await store.set_partner(_KEY_A, partner_id=1, partner_name="Cliente")
        await store.add_lines(_KEY_A, [(3, 1.0)])
        cart = await store.add_lines(_KEY_A, [(3, 2.0)])

        assert len(cart.lines) == 1
        assert cart.lines[0].product_id == 3
        assert cart.lines[0].qty == 3.0

    asyncio.run(run())


def test_add_lines_without_partner_fails() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        with pytest.raises(ValueError, match="No hay cliente"):
            await store.add_lines(_KEY_A, [(1, 1.0)])

    asyncio.run(run())


def test_get_cart_empty() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        cart = await store.get_cart(_KEY_A)
        assert cart.partner_id is None
        assert cart.lines == []

    asyncio.run(run())


def test_clear_cart_idempotent() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        await store.set_partner(_KEY_A, partner_id=1, partner_name="Cliente")
        await store.add_lines(_KEY_A, [(1, 1.0)])
        await store.clear(_KEY_A)
        assert await store.get_cart(_KEY_A) == await store.get_cart(_KEY_A)

        cart = await store.get_cart(_KEY_A)
        assert cart.partner_id is None
        assert cart.lines == []

        await store.clear(_KEY_A)

    asyncio.run(run())


def test_separate_auth_keys() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        await store.set_partner(_KEY_A, partner_id=1, partner_name="A")
        await store.add_lines(_KEY_A, [(1, 1.0)])
        await store.set_partner(_KEY_B, partner_id=2, partner_name="B")
        await store.add_lines(_KEY_B, [(2, 3.0)])

        cart_a = await store.get_cart(_KEY_A)
        cart_b = await store.get_cart(_KEY_B)

        assert cart_a.partner_id == 1
        assert [(line.product_id, line.qty) for line in cart_a.lines] == [(1, 1.0)]
        assert cart_b.partner_id == 2
        assert [(line.product_id, line.qty) for line in cart_b.lines] == [(2, 3.0)]

    asyncio.run(run())


def test_add_lines_rejects_non_positive_quantity() -> None:
    async def run() -> None:
        store = InMemoryCartStore()
        await store.set_partner(_KEY_A, partner_id=1, partner_name="Cliente")
        with pytest.raises(ValueError, match="quantity"):
            await store.add_lines(_KEY_A, [(1, 0.0)])

    asyncio.run(run())
