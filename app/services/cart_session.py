"""Lógica de carrito admin (cliente + líneas de producto)."""

from __future__ import annotations

import json
from typing import Any

from app.clients.odoo_json2 import OdooJson2Client
from app.services.cart import cart_store, cart_response
from app.services.cart.base import AdminCart, CartStoreKey, empty_admin_cart
from app.services.catalog import read_products_by_ids


async def _fetch_partner_name(odoo: OdooJson2Client, partner_id: int) -> str:
    partners = await odoo.call(
        "res.partner",
        "read",
        ids=[partner_id],
        fields=["name"],
    )
    if not partners:
        raise ValueError(f"No existe un cliente con id={partner_id}.")
    return str(partners[0].get("name") or "")


async def _cart_response(
    cart: AdminCart,
    odoo: OdooJson2Client,
    *,
    message: str | None = None,
) -> dict[str, Any]:
    products_by_id: dict[int, dict[str, Any]] = {}
    if cart.lines:
        product_ids = [line.product_id for line in cart.lines]
        products_by_id = await read_products_by_ids(odoo, product_ids=product_ids)
    return cart_response(cart, products_by_id=products_by_id, message=message)


async def create_cart_session(
    key: CartStoreKey,
    odoo: OdooJson2Client,
    *,
    partner_id: int,
) -> dict[str, Any]:
    partner_name = await _fetch_partner_name(odoo, partner_id)
    cart = await cart_store.set_partner(
        key,
        partner_id=partner_id,
        partner_name=partner_name,
    )
    return cart_response(
        cart,
        message=f"Carrito creado para el cliente {partner_name} (id={partner_id}).",
    )


async def add_to_cart(
    key: CartStoreKey,
    odoo: OdooJson2Client,
    *,
    product_id: int,
    quantity: float,
) -> dict[str, Any]:
    cart = await cart_store.add_lines(key, [(product_id, quantity)])
    return await _cart_response(cart, odoo, message="Producto añadido al carrito.")


def _parse_lines_json(lines_json: str) -> list[tuple[int, float]]:
    try:
        raw = json.loads(lines_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "lines_json debe ser un JSON válido: "
            '\'[{"product_id": 7, "qty": 2.0}, ...]\'.'
        ) from exc
    if not isinstance(raw, list) or not raw:
        raise ValueError("lines_json debe ser una lista no vacía de líneas.")

    lines: list[tuple[int, float]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ValueError(f"Línea {index}: se esperaba un objeto con product_id y qty.")
        product_id = item.get("product_id")
        qty = item.get("qty")
        if not isinstance(product_id, int):
            raise ValueError(f"Línea {index}: product_id debe ser un entero.")
        if not isinstance(qty, (int, float)):
            raise ValueError(f"Línea {index}: qty debe ser numérico.")
        lines.append((product_id, float(qty)))
    return lines


async def add_to_cart_lines(
    key: CartStoreKey,
    odoo: OdooJson2Client,
    *,
    lines_json: str,
) -> dict[str, Any]:
    lines = _parse_lines_json(lines_json)
    cart = await cart_store.add_lines(key, lines)
    return await _cart_response(
        cart,
        odoo,
        message=f"{len(lines)} línea(s) añadida(s) al carrito.",
    )


async def get_cart(key: CartStoreKey, odoo: OdooJson2Client) -> dict[str, Any]:
    cart = await cart_store.get_cart(key)
    return await _cart_response(cart, odoo)


async def clear_cart(key: CartStoreKey) -> dict[str, Any]:
    await cart_store.clear(key)
    return cart_response(empty_admin_cart(), message="Carrito vaciado.")
