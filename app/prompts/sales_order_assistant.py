"""Prompt de asistente de ventas: carrito y creación de pedidos."""

from __future__ import annotations

from fastmcp.prompts import Message

from app.server import mcp


@mcp.prompt(
    name="sales_order_assistant",
    description=(
        "Guía para crear pedidos de venta: seleccionar cliente, crear carrito, "
        "añadir productos, confirmar con get_cart y crear pedido con create_order."
    ),
)
def sales_order_assistant() -> list[Message]:
    lines = [
        "Ayuda al usuario a crear un pedido de venta confirmado en Odoo.",
        "El carrito se asocia a la sesión mediante la cabecera HTTP auth-key; "
        "no hace falta pasar un identificador manual en las tools de carrito.",
        "Flujo obligatorio:",
        "1. Buscar y seleccionar el cliente con read_customers (o app://customers).",
        "2. Llamar a create_cart(partner_id) antes de añadir el primer producto.",
        "3. Añadir productos con add_to_cart (product_id + quantity) o varias líneas con lines_json.",
        "4. Cuando el usuario quiera crear el pedido, llama primero a get_cart y muestra el resumen "
        "(cliente, líneas, cantidades) para que confirme.",
        "5. Tras la confirmación del usuario, llama a create_order(ref opcional); "
        "si tiene éxito, el carrito se vacía automáticamente.",
        "El usuario puede indicar cliente y productos en el mismo mensaje: "
        "resuelve el cliente, crea el carrito y añade los productos en ese orden.",
        "Siempre debe haber un cliente (create_cart) antes del primer producto.",
        "Para atender a otro cliente, primero termina el pedido en curso (create_order) "
        "o abandona la sesión (clear_cart).",
        "Para consultar el carrito actual usa get_cart; para vaciarlo manualmente usa clear_cart.",
    ]
    return [Message("\n".join(lines))]
