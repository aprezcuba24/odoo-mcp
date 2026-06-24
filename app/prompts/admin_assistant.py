"""Prompt de asistente admin: clientes Odoo (tools y resources MCP)."""

from __future__ import annotations

from fastmcp.prompts import Message

from app.server import mcp


@mcp.prompt(
    name="find_client_assistant",
    description=(
        "Guía para consultar clientes Odoo (resource app://customers en primer lugar; "
        "si no hay resources/read, read_customers). "
        "Listado sin filtros o búsqueda por nombre, NIF/CIF o email."
    ),
)
def find_client_assistant() -> list[Message]:
    lines = [
        "Ayuda al usuario a consultar clientes Odoo (res.partner con customer_rank > 0).",
        "Para listar todos los clientes, lee app://customers; "
        "si el cliente no soporta resources/read, usa read_customers() sin argumentos.",
        "Para buscar con filtros, lee app://customers?name=... (exacto), "
        "?vat=... (NIF/CIF) o ?email=...; "
        "si no hay resources/read, usa read_customers con el mismo parámetro.",
        "Interpreta el campo count de la respuesta: "
        "count=0 indica que no hay coincidencias; "
        "count=1 devuelve id, name, email, phone, vat; "
        "count>1 lista candidatos para que el usuario elija.",
        "Prioriza Resources app:// y usa read_customers solo como respaldo.",
    ]
    return [Message("\n".join(lines))]
