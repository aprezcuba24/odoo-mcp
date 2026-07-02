"""Herramienta de creación de pedidos confirmados desde el carrito."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services.cart import cart_store, lines_payload
from app.services.orders import create_confirmed_order
from app.utils.app_key_codec import resolve_app_context

_BUILD_CART_AGENT_HINT = (
    "Extrae cliente y productos del mensaje o conversación; "
    "llama create_cart y add_to_cart; muestra el resumen y pide confirmación. "
    "No indiques al usuario que no puedes registrar el pedido."
)


@mcp.tool(
    name="create_order",
    description=(
        "Crea un pedido de venta confirmado en Odoo desde el carrito actual "
        "(sale.order.api_create_confirmed_order). "
        "Solo invocar cuando el carrito ya tiene cliente y líneas, y el usuario confirmó explícitamente "
        "en un mensaje posterior al resumen de add_to_cart. "
        "No invocar con carrito vacío: si el usuario pide registrar compra, construye el carrito "
        "con create_cart y add_to_cart primero. "
        "Nunca llames create_order automáticamente ni en el mismo turno en que añadiste productos. "
        "Parámetro opcional: ref (referencia del cliente, client_order_ref). "
        "Si el pedido se crea correctamente, vacía el carrito. "
        "Si no hay cliente: ok=false, error=no_customer (sigue _agent para construir el carrito). "
        "Si no hay líneas: ok=false, error=empty_cart (sigue _agent para construir el carrito)."
    ),
)
async def create_order_tool(
    ref: str | None = None,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    key = resolve_app_context().cart_store_key()
    cart = await cart_store.get_cart(key)

    if cart.partner_id is None:
        return {
            "ok": False,
            "error": "no_customer",
            "message": (
                "No hay cliente en el carrito. "
                "Construye el carrito: busca el cliente con read_customers, "
                "desambigua si hace falta, y llama create_cart."
            ),
            "_agent": {
                "next": "build_cart_from_context",
                "hint": _BUILD_CART_AGENT_HINT,
            },
        }

    if not cart.lines:
        return {
            "ok": False,
            "error": "empty_cart",
            "message": (
                "El carrito no tiene productos. "
                "Construye el carrito con los datos del usuario: resuelve productos en el catálogo "
                "y añádelos con add_to_cart."
            ),
            "partner_id": cart.partner_id,
            "partner_name": cart.partner_name,
            "lines": [],
            "_agent": {
                "next": "build_cart_from_context",
                "hint": _BUILD_CART_AGENT_HINT,
            },
        }

    lines = lines_payload(cart.lines)
    order = await create_confirmed_order(
        _odoo,
        partner_id=cart.partner_id,
        lines=lines,
        ref=ref,
    )
    await cart_store.clear(key)

    return {
        "ok": True,
        "order": order,
        "cart_cleared": True,
    }
