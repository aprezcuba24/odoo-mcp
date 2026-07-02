"""Herramientas de carrito admin (cliente + productos por auth-key)."""

from __future__ import annotations

from typing import Any

from uncalled_for import Depends

from app.clients.odoo_json2 import OdooJson2Client
from app.server import get_odoo_client, mcp
from app.services import cart_session
from app.utils.app_key_codec import resolve_app_context


@mcp.tool(
    name="create_cart",
    description=(
        "Crea un carrito nuevo asociado a un cliente Odoo (res.partner). "
        "Obligatorio antes de añadir el primer producto. "
        "Solo llama tras selección inequívoca del cliente: si read_customers devuelve count>1 "
        "o _agent.next es disambiguate, lista candidatos con id, nombre, teléfono y dirección "
        "y espera elección del usuario (suele indicar el id). "
        "El carrito se identifica con la cabecera HTTP auth-key (backend + token). "
        "Parámetro: partner_id (id del cliente). "
        "Falla si ya hay un carrito activo con otro cliente; usa create_order o clear_cart primero."
    ),
)
async def create_cart_tool(
    partner_id: int,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    key = resolve_app_context().cart_store_key()
    return await cart_session.create_cart_session(key, _odoo, partner_id=partner_id)


@mcp.tool(
    name="add_to_cart",
    description=(
        "Añade uno o varios productos al carrito del servidor MCP y devuelve el carrito "
        "completo enriquecido (cliente, líneas con nombre/precio/subtotal, amount_total). "
        "Usa esta respuesta como resumen de revisión para el usuario; no hace falta llamar "
        "get_cart después. Requiere create_cart previo con un cliente. "
        "product_id debe obtenerse del catálogo (app://catalog/products, read_catalog_products "
        "o read_catalog_product); no inventes IDs. Si el usuario describe un producto por nombre, "
        "busca primero en el catálogo; si hay varias coincidencias o _agent.next es disambiguate, "
        "lista candidatos con id y stock y espera elección (suele ser por id) antes de add_to_cart. "
        "Modo simple: product_id y quantity (> 0); suma cantidad si el producto ya está. "
        "Modo múltiple: lines_json como cadena JSON "
        '[{"product_id": 7, "qty": 2.0}, {"product_id": 12, "qty": 1.0}]. '
        "Tras añadir productos, muestra el resumen al usuario y espera confirmación explícita "
        "en un mensaje posterior antes de create_order."
    ),
)
async def add_to_cart_tool(
    product_id: int | None = None,
    quantity: float | None = None,
    lines_json: str | None = None,
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    key = resolve_app_context().cart_store_key()

    if lines_json is not None:
        if product_id is not None or quantity is not None:
            raise ValueError(
                "Usa product_id+quantity o lines_json, no ambos a la vez."
            )
        return await cart_session.add_to_cart_lines(
            key, _odoo, lines_json=lines_json
        )

    if product_id is None or quantity is None:
        raise ValueError(
            "Indica product_id y quantity, o lines_json con varias líneas."
        )
    return await cart_session.add_to_cart(
        key,
        _odoo,
        product_id=product_id,
        quantity=quantity,
    )


@mcp.tool(
    name="get_cart",
    description=(
        "Consulta opcional del carrito actual (cabecera HTTP auth-key). "
        "Devuelve el mismo formato enriquecido que add_to_cart (cliente, líneas con "
        "nombre/precio/subtotal, amount_total). Úsalo solo si necesitas refrescar el estado "
        "sin añadir productos; tras add_to_cart no es necesario."
    ),
)
async def get_cart_tool(
    _odoo: OdooJson2Client = Depends(get_odoo_client),
) -> dict[str, Any]:
    key = resolve_app_context().cart_store_key()
    return await cart_session.get_cart(key, _odoo)


@mcp.tool(
    name="clear_cart",
    description=(
        "Vacía el carrito del dispositivo actual (cabecera HTTP auth-key), "
        "incluyendo el cliente asignado. Idempotente si ya estaba vacío."
    ),
)
async def clear_cart_tool() -> dict[str, Any]:
    key = resolve_app_context().cart_store_key()
    return await cart_session.clear_cart(key)
