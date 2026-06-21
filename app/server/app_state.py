"""Process-wide references set during FastMCP lifespan (HTTP client pool)."""

from __future__ import annotations

import asyncio

import httpx

from app.clients.odoo_json2 import OdooJson2Client, raw_api_key
from app.utils.app_key_codec import resolve_app_context


class ClientRegistry:
    """Lazy pool of httpx clients keyed by backend base URL."""

    __slots__ = ("_clients", "_lock", "_timeout")

    def __init__(self, *, timeout: float) -> None:
        self._timeout = timeout
        self._lock = asyncio.Lock()
        self._clients: dict[str, httpx.AsyncClient] = {}

    async def get_client(self, base_url: str) -> httpx.AsyncClient:
        key = base_url.rstrip("/")
        async with self._lock:
            client = self._clients.get(key)
            if client is not None:
                return client

            client = httpx.AsyncClient(base_url=key, timeout=self._timeout)
            self._clients[key] = client
            return client

    async def close_all(self) -> None:
        async with self._lock:
            clients = list(self._clients.values())
            self._clients.clear()

        for client in clients:
            await client.aclose()


class AppState:
    __slots__ = ("registry",)

    def __init__(self) -> None:
        self.registry: ClientRegistry | None = None


app_state = AppState()


async def get_odoo_client(*, lang: str = "es_ES") -> OdooJson2Client:
    """Build an Odoo JSON-2 client from the current request auth-key context."""
    registry = app_state.registry
    if registry is None:
        raise RuntimeError("API client not initialized; server lifespan did not start.")
    ctx = resolve_app_context()
    client = await registry.get_client(ctx.base_url)
    return OdooJson2Client(
        client=client,
        base_url=ctx.base_url,
        api_key=raw_api_key(ctx.user_token),
        database=ctx.database,
        lang=lang,
    )
