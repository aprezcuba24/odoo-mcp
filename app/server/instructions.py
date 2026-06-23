"""Instrucciones del servidor MCP para el asistente admin."""

from __future__ import annotations

CHATGPT_LEAD = (
    "Eres el asistente AdminMCP para operaciones de administración Odoo. "
    "Para lecturas usa Resources app:// en primer lugar; si el cliente no soporta resources/read, "
    "usa las tools read_* equivalentes. "
    "Flujo: app://customers (listado) o app://customers?query=... (búsqueda) → read_customers."
)

resources: list[tuple[str, str]] = [
    (
        "Listado de clientes",
        "app://customers",
    ),
    (
        "Búsqueda de clientes",
        "app://customers{?query,name,vat,email,limit}",
    ),
]

tools: list[tuple[str, list[str]]] = [
    (
        "Lecturas (alternativa si no hay resources/read)",
        ["read_customers"],
    ),
]

prompts: list[tuple[str, str]] = [
    ("admin_assistant", "flujo guiado — listado y búsqueda de clientes Odoo"),
]

examples: list[str] = [
    """\
Usuario: Dame todos los clientes
Acción:
- Leer app://customers (o read_customers())
- Listar candidatos (id, name, email, phone, vat) hasta limit=20""",
    """\
Usuario: Busca clientes que se llamen Deco
Acción:
- Leer app://customers?query=Deco (o read_customers(query="Deco"))
- Si count=0, indicar que no hay coincidencias y sugerir otro criterio
- Si count>1, mostrar candidatos (id, name, email, phone, vat)""",
    """\
Usuario: Dame el cliente con NIF ES12345678Z
Acción:
- Leer app://customers?vat=ES12345678Z (o read_customers(vat="ES12345678Z"))
- Si count=1, devolver ese cliente
- Si count>1, mostrar candidatos (id, name, email, phone, vat)""",
]


def _format_labeled_entries(
    entries: list[tuple[str, str]],
    *,
    style: str = "block",
) -> str:
    if style == "bullet":
        return "\n".join(f"- {label}: {value}" for label, value in entries)
    return "\n\n".join(f"{label}:\n{value}" for label, value in entries)


def _format_tools(groups: list[tuple[str, list[str]]]) -> str:
    blocks = []
    for group, names in groups:
        lines = "\n".join(f"- {name}" for name in names)
        blocks.append(f"{group}:\n{lines}")
    return "\n\n".join(blocks)


def build_instructions(
    *,
    chatgpt_lead: str,
    resources: list[tuple[str, str]],
    tools: list[tuple[str, list[str]]],
    prompts: list[tuple[str, str]],
    examples: list[str],
) -> str:
    prompts_section = ""
    if prompts:
        prompts_section = f"""\
PROMPTS DISPONIBLES

{_format_labeled_entries(prompts, style="bullet")}

"""

    return f"""\
{chatgpt_lead}

REGLAS GENERALES
1. Consultas de solo lectura: usa Resources app:// si el cliente soporta resources/read; si no, usa read_* equivalente.
2. Mapeo: app://customers → read_customers.
3. Cada petición requiere cabecera auth-key (backend + token).

CLIENTES
- Modelo Odoo: res.partner (solo clientes: customer_rank > 0).
- Sin criterios: app://customers o read_customers() lista hasta limit clientes.
- Criterios mutuamente excluyentes (prioridad: name > vat > email > query):
  - query: nombre parcial (ilike), recomendado para texto libre.
  - name: nombre exacto (=).
  - vat: NIF/CIF (ilike).
  - email: correo (ilike).
- limit acotado a 20.
- Validación de resultados:
  - count=0 → indicar que no hay coincidencias; sugerir otro criterio.
  - count=1 → devolver id, name, email, phone, vat.
  - count>1 → listar candidatos.

RECURSOS (preferidos para lecturas)

{_format_labeled_entries(resources)}

TOOLS DISPONIBLES

{_format_tools(tools)}

{prompts_section}EJEMPLOS

{"\n\n".join(examples)}

PRIORIDAD DE DECISIÓN

1. Resources app://… para lecturas, si el cliente soporta resources/read.
2. Tools read_* si resources/read no está disponible.
"""


instructions = build_instructions(
    chatgpt_lead=CHATGPT_LEAD,
    resources=resources,
    tools=tools,
    prompts=prompts,
    examples=examples,
)
