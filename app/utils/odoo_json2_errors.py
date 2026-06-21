"""Map Odoo JSON-2 HTTP error responses to typed exceptions."""

from __future__ import annotations

import json
from typing import Any

from app.utils.exceptions import (
    AppApiError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationApiError,
)


def body_from_content(content: bytes) -> dict[str, Any] | None:
    try:
        raw = json.loads(content.decode())
        return raw if isinstance(raw, dict) else None
    except Exception:
        return None


def message_from_error_body(body: dict[str, Any] | None, fallback: str) -> str:
    if not body:
        return fallback.strip()
    message = body.get("message")
    if isinstance(message, str) and message:
        return message
    name = body.get("name")
    if isinstance(name, str) and name:
        return name
    return fallback.strip()


def raise_odoo_http(*, status_code: int, content: bytes, fallback_text: str) -> None:
    """Raise a typed ``AppApiError`` for Odoo JSON-2 error responses."""
    body = body_from_content(content)
    msg = message_from_error_body(body, fallback_text)

    if status_code == 401:
        raise UnauthorizedError(msg or "Unauthorized", status_code=status_code, body=body)
    if status_code == 403:
        raise ForbiddenError(msg or "Forbidden", status_code=status_code, body=body)
    if status_code == 404:
        raise NotFoundError(msg or "Not found", status_code=status_code, body=body)
    if status_code == 422:
        raise ValidationApiError(msg or "Validation error", status_code=status_code, body=body)
    raise AppApiError(msg or f"HTTP {status_code}", status_code=status_code, body=body)
