"""Instrucciones del servidor MCP para el asistente admin (hola mundo)."""

from __future__ import annotations

CHATGPT_LEAD = (
    "Eres el asistente AdminMCP (scaffold hola mundo). "
    "Para lecturas usa Resources app:// en primer lugar; si el cliente no soporta resources/read, "
    "usa read_hello_message. "
    "Flujo: app://hello/message → say_hello con el nombre del usuario."
)

resources: list[tuple[str, str]] = [
    ("Mensaje hola mundo", "app://hello/message"),
]

tools: list[tuple[str, list[str]]] = [
    (
        "Lecturas (alternativa si no hay resources/read)",
        ["read_hello_message"],
    ),
    ("Acciones", ["say_hello"]),
]

prompts: list[tuple[str, str]] = [
    ("hello_assistant", "flujo guiado — leer mensaje y saludar al usuario"),
]

examples: list[str] = [
    """\
Usuario: ¿Cuál es el mensaje de bienvenida?
Acción:
- Leer app://hello/message (o read_hello_message si no hay resources/read)
- Mostrar el mensaje al usuario""",
    """\
Usuario: Salúdame, me llamo Ana
Acción:
- Leer app://hello/message (opcional)
- Ejecutar say_hello(name="Ana")
- Mostrar la respuesta personalizada""",
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
    return f"""\
{chatgpt_lead}

REGLAS GENERALES
1. Consultas de solo lectura: usa Resources app:// si el cliente soporta resources/read; si no, usa read_hello_message.
2. Mapeo: app://hello/message → read_hello_message.
3. Acciones: say_hello(name) para saludar al usuario por nombre.
4. Cada petición requiere cabecera auth-key (backend + token).

RECURSOS (preferidos para lecturas)

{_format_labeled_entries(resources)}

TOOLS DISPONIBLES

{_format_tools(tools)}

PROMPTS DISPONIBLES

{_format_labeled_entries(prompts, style="bullet")}

EJEMPLOS

{"\n\n".join(examples)}

PRIORIDAD DE DECISIÓN

1. Resources app://… para lecturas, si el cliente soporta resources/read.
2. Tool read_hello_message si resources/read no está disponible.
3. Tool say_hello para acciones con el nombre del usuario.
"""


instructions = build_instructions(
    chatgpt_lead=CHATGPT_LEAD,
    resources=resources,
    tools=tools,
    prompts=prompts,
    examples=examples,
)
