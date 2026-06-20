"""Prompt hola mundo — guía para leer mensaje y saludar."""

from __future__ import annotations

from fastmcp.prompts import Message

from app.server import mcp


@mcp.prompt(
    name="hello_assistant",
    description=(
        "Guía para leer app://hello/message (o read_hello_message) "
        "y saludar al usuario con say_hello."
    ),
)
def hello_assistant() -> list[Message]:
    lines = [
        "Ayuda al usuario con el ejemplo hola mundo de AdminMCP.",
        "Primero lee app://hello/message para mostrar el mensaje de bienvenida.",
        "Si el cliente no soporta resources/read, usa read_hello_message().",
        "Cuando el usuario indique su nombre, llama a say_hello(name=...) para un saludo personalizado.",
        "Muestra el campo message de la respuesta; no expongas detalles técnicos del backend salvo que lo pidan.",
    ]
    return [Message("\n".join(lines))]
