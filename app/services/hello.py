"""Hello world service — shared logic for resource and tools."""

from __future__ import annotations

from typing import Any

from app.utils.shop_key_codec import ShopContext


def build_hello_payload(ctx: ShopContext, *, name: str | None = None) -> dict[str, Any]:
    """Build a hello-world payload including backend from shop-key context."""
    if name:
        message = f"Hola, {name}!"
    else:
        message = "Hola, mundo!"

    return {
        "message": message,
        "name": name,
        "backend": ctx.base_url,
    }
