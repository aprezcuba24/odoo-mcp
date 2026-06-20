"""Hello world service — shared logic for resource and tools."""

from __future__ import annotations

from typing import Any

from app.utils.app_key_codec import AppContext


def build_hello_payload(ctx: AppContext, *, name: str | None = None) -> dict[str, Any]:
    """Build a hello-world payload including backend from auth-key context."""
    if name:
        message = f"Hola, {name}!"
    else:
        message = "Hola, mundo!"

    return {
        "message": message,
        "name": name,
        "backend": ctx.base_url,
    }
