"""Prompt de asistente admin: clientes Odoo (tools y resources MCP)."""

from __future__ import annotations

from fastmcp.prompts import Message

from app.server import mcp


@mcp.prompt(
    name="find_client_assistant",
    description=(
        "Guía para consultar clientes Odoo (resource app://customers en primer lugar; "
        "si no hay resources/read, read_customers). "
        "Listado sin filtros o búsqueda por texto libre (nombre, teléfono, dirección)."
    ),
)
def find_client_assistant() -> list[Message]:
    lines = [
        "Ayuda al usuario a consultar clientes Odoo (res.partner vía api_search_customers).",
        "Este paso es prerrequisito del flujo de pedidos: no llames create_cart hasta "
        "tener un partner_id elegido de forma inequívoca.",
        "Para listar todos los clientes, lee app://customers; "
        "si el cliente no soporta resources/read, usa read_customers() sin argumentos.",
        "Para buscar, lee app://customers?query=... (texto libre en nombre, teléfono y dirección); "
        "si no hay resources/read, usa read_customers(query=...).",
        "Interpreta el campo count de la respuesta:",
        "count=0 → no hay coincidencias; sugiere otro criterio (nombre más específico, teléfono, dirección).",
        "count=1 → devuelve id, name, phone, order_bridge_registered, order_bridge_phone_validated, address.",
        "count>1 → lista candidatos numerados con nombre, teléfono y dirección "
        "(street, neighborhood_name, municipality_name, state; omitir campos vacíos) "
        "para que el usuario identifique al correcto; espera su elección.",
        "Prioriza Resources app:// y usa read_customers solo como respaldo.",
    ]
    return [Message("\n".join(lines))]
