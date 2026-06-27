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
        "Nunca confirmes la compra automáticamente.",
        "El carrito se asocia a la sesión mediante la cabecera HTTP auth-key; "
        "no hace falta pasar un identificador manual en las tools de carrito.",
        "Flujo obligatorio:",
        "1. Buscar el cliente con read_customers (o app://customers). "
        "Si count=0, informa que no hay coincidencias y pide otro criterio; no avances. "
        "Si count>1 o el cliente no es identificable, lista candidatos numerados con "
        "nombre, teléfono y dirección (street, neighborhood_name, municipality_name, state) "
        "y espera a que el usuario elija; no asumas el primero ni el más parecido.",
        "2. Llama a create_cart(partner_id) solo tras una elección inequívoca del cliente.",
        "3. Resolver productos en el catálogo: app://catalog/products, read_catalog_products(search=...) "
        "o read_catalog_product(product_id). No inventes product_id ni precios. "
        "Al mostrar productos, incluye siempre available_qty (stock disponible) y qty_on_hand (existencias).",
        "4. Si el usuario describe un producto por nombre, busca en catálogo; "
        "con varias coincidencias muestra opciones con stock y pide confirmación.",
        "5. Añadir productos con add_to_cart (product_id + quantity) o varias líneas con lines_json.",
        "6. Llama siempre a get_cart y presenta el resumen completo al usuario "
        "(cliente, cada línea con product_id y cantidad, totales).",
        "7. Espera confirmación explícita, modificación o cancelación del usuario. "
        "No llames create_order en el mismo turno en que añadiste productos.",
        "8. Solo tras confirmación explícita (p. ej. 'sí, confirma'), llama create_order(ref opcional); "
        "si tiene éxito, el carrito se vacía automáticamente.",
        "El usuario puede indicar cliente y productos en el mismo mensaje: "
        "resuelve y desambigua el cliente, crea el carrito, consulta catálogo y añade productos; "
        "pero get_cart y create_order van en turnos separados con confirmación.",
        "Siempre debe haber un cliente (create_cart) antes del primer producto.",
        "Para atender a otro cliente, primero termina el pedido en curso (create_order) "
        "o abandona la sesión (clear_cart).",
        "Para consultar el carrito actual usa get_cart; para vaciarlo manualmente usa clear_cart.",
    ]
    return [Message("\n".join(lines))]
