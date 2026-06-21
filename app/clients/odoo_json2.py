"""Async client for Odoo 19 JSON-2 API (POST /json/2/{model}/{method})."""

from __future__ import annotations

import re
from typing import Any

import httpx

from app.utils.odoo_json2_errors import raise_odoo_http

USER_AGENT = "admin-mcp/0.1.0"
_BEARER_PREFIX_RE = re.compile(r"^bearer\s+", re.IGNORECASE)


def raw_api_key(user_token: str) -> str:
    """Strip optional ``Bearer`` prefix from the auth-key API key segment."""
    return _BEARER_PREFIX_RE.sub("", user_token.strip())


class OdooJson2Client:
    """Call Odoo ORM methods via the official JSON-2 HTTP API."""

    __slots__ = ("_base_url", "_client", "_api_key", "_database", "_lang")

    def __init__(
        self,
        client: httpx.AsyncClient,
        *,
        base_url: str,
        api_key: str,
        database: str | None = None,
        lang: str = "es_ES",
    ) -> None:
        self._client = client
        self._base_url = base_url.rstrip("/")
        self._api_key = raw_api_key(api_key)
        self._database = database
        self._lang = lang

    def _request_headers(self, *, authenticated: bool) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": USER_AGENT,
        }
        if authenticated:
            headers["Authorization"] = f"bearer {self._api_key}"
        if self._database:
            headers["X-Odoo-Database"] = self._database
        return headers

    async def call(self, model: str, method: str, **params: Any) -> Any:
        """Invoke a public ORM method via ``POST /json/2/{model}/{method}``."""
        if "context" not in params:
            params = {**params, "context": {"lang": self._lang}}

        response = await self._client.post(
            f"/json/2/{model}/{method}",
            json=params,
            headers=self._request_headers(authenticated=True),
        )
        if not response.is_success:
            raise_odoo_http(
                status_code=response.status_code,
                content=response.content,
                fallback_text=response.text,
            )
        return response.json()

    async def healthcheck(self) -> Any:
        """Fetch Odoo version info via ``GET /web/version`` (no auth)."""
        response = await self._client.get(
            "/web/version",
            headers=self._request_headers(authenticated=False),
        )
        if not response.is_success:
            raise_odoo_http(
                status_code=response.status_code,
                content=response.content,
                fallback_text=response.text,
            )
        return response.json()
