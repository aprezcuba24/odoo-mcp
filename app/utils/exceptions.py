"""Typed errors for AdminMCP."""

from __future__ import annotations

from typing import Any


class AdminMcpError(Exception):
    """Base error for this package."""


class MissingShopKeyError(AdminMcpError):
    """MCP request did not carry shop-key via header or query param."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(message or "Missing shop-key.", *args)


class InvalidShopKeyError(MissingShopKeyError):
    """shop-key present but not valid base64(BASE_URL|user_token)."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(
            message or "Invalid shop-key: expected base64(BASE_URL|user_token).",
            *args,
        )


class AmbiguousShopKeyError(MissingShopKeyError):
    """Both shop-key header and key query param were sent."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(message or "Ambiguous shop-key", *args)


class AdminApiError(AdminMcpError):
    """REST API returned an error response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        body: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class UnauthorizedError(AdminApiError):
    """401 — invalid or missing Bearer token."""
