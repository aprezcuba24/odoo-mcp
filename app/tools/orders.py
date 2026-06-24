"""Herramienta de creación de pedidos confirmados desde el carrito."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services import cart_session
from app.services.cart import cart_store, lines_payload
from app.services.orders import create_confirmed_order
from app.utils.app_key_codec import resolve_app_context


@mcp.tool(
    name="create_order",
    description=(
        "Crea un pedido de venta confirmado en Odoo desde el carrito actual "
        "(sale.order.api_create_confirmed_order). "
        "Antes de llamar a esta tool, muestra al usuario el resumen con get_cart para confirmación. "
        "Parámetro opcional: ref (referencia del cliente, client_order_ref). "
        "Si el pedido se crea correctamente, vacía el carrito. "
        "Si no hay cliente: ok=false, error=no_customer. "
        "Si no hay líneas: ok=false, error=empty_cart."
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
                "Busca un cliente con read_customers y llama a create_cart antes de crear el pedido."
            ),
        }

    if not cart.lines:
        return {
            "ok": False,
            "error": "empty_cart",
            "message": (
                "El carrito no tiene productos. "
                "Añade productos con add_to_cart antes de crear el pedido."
            ),
            "partner_id": cart.partner_id,
            "partner_name": cart.partner_name,
            "lines": [],
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
