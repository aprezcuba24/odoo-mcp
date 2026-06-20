"""Process-wide references set during FastMCP lifespan (HTTP client pool)."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from app.utils.app_key_codec import resolve_app_context


@dataclass(frozen=True, slots=True)
class AppClientRef:
    """Holds an httpx client for the decoded backend without ``__aenter__``."""

    client: httpx.AsyncClient
    base_url: str


@dataclass(frozen=True, slots=True)
class AuthenticatedAppRef:
    """Per-request httpx client for the decoded backend plus Bearer token."""

    client: httpx.AsyncClient
    base_url: str
    bearer_token: str


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


async def get_app_api() -> AppClientRef:
    registry = app_state.registry
    if registry is None:
        raise RuntimeError("API client not initialized; server lifespan did not start.")
    ctx = resolve_app_context()
    client = await registry.get_client(ctx.base_url)
    return AppClientRef(client=client, base_url=ctx.base_url)


async def get_authenticated_app_api() -> AuthenticatedAppRef:
    registry = app_state.registry
    if registry is None:
        raise RuntimeError("API client not initialized; server lifespan did not start.")
    ctx = resolve_app_context()
    client = await registry.get_client(ctx.base_url)
    return AuthenticatedAppRef(
        client=client,
        base_url=ctx.base_url,
        bearer_token=ctx.bearer_token,
    )
