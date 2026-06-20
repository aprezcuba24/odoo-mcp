"""Typed errors for AdminMCP."""

from __future__ import annotations

from typing import Any


class AppMcpError(Exception):
    """Base error for this package."""


class MissingAuthKeyError(AppMcpError):
    """MCP request did not carry auth-key via header or query param."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(message or "Missing auth-key.", *args)


class InvalidAuthKeyError(MissingAuthKeyError):
    """auth-key present but not valid base64(BASE_URL|user_token)."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(
            message or "Invalid auth-key: expected base64(BASE_URL|user_token).",
            *args,
        )


class AmbiguousAuthKeyError(MissingAuthKeyError):
    """Both auth-key header and key query param were sent."""

    def __init__(self, message: str | None = None, *args: object) -> None:
        super().__init__(message or "Ambiguous auth-key", *args)


class AppApiError(AppMcpError):
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


class UnauthorizedError(AppApiError):
    """401 — invalid or missing Bearer token."""
