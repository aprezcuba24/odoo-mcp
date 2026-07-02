"""Prompt de asistente de ventas: carrito y creación de pedidos."""

from __future__ import annotations

from fastmcp.prompts import Message

from app.server import mcp


@mcp.prompt(
    name="sales_order_assistant",
    description=(
        "Guía para crear pedidos de venta: seleccionar cliente, crear carrito, "
        "añadir productos, revisar resumen de add_to_cart y crear pedido con create_order."
    ),
)
def sales_order_assistant() -> list[Message]:
    lines = [
        "Ayuda al usuario a crear un pedido de venta confirmado en Odoo.",
        "Nunca confirmes la compra automáticamente.",
        "El carrito se asocia a la sesión mediante la cabecera HTTP auth-key; "
        "no hace falta pasar un identificador manual en las tools de carrito.",
        "Flujo en dos pasos para el usuario:",
        "Paso 1 — Construir carrito (un turno):",
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
        "5. Añadir productos con add_to_cart (product_id + quantity) o varias líneas con lines_json. "
        "Muestra al usuario la respuesta de add_to_cart (cliente, líneas con nombre/precio/subtotal, "
        "amount_total) y pide confirmación. No llames create_order en este turno.",
        "Paso 2 — Confirmar pedido (otro turno):",
        "6. Solo tras confirmación explícita (p. ej. 'sí, confirma'), llama create_order(ref opcional); "
        "si tiene éxito, el carrito se vacía automáticamente.",
        "El usuario puede indicar cliente y productos en el mismo mensaje: "
        "resuelve y desambigua el cliente, crea el carrito, consulta catálogo y añade productos; "
        "pero create_order va en un turno separado con confirmación.",
        "Siempre debe haber un cliente (create_cart) antes del primer producto.",
        "Para atender a otro cliente, primero termina el pedido en curso (create_order) "
        "o abandona la sesión (clear_cart).",
        "get_cart es opcional; úsalo solo si necesitas refrescar el estado sin añadir productos.",
        "Para vaciar el carrito manualmente usa clear_cart.",
    ]
    return [Message("\n".join(lines))]
