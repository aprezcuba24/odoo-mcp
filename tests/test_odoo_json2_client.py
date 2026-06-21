"""Unit tests for Odoo JSON-2 client."""

from __future__ import annotations

import asyncio
import json

import httpx
import pytest

from app.clients.odoo_json2 import OdooJson2Client, raw_api_key
from app.utils.exceptions import (
    AppApiError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationApiError,
)

_BASE = "https://odoo.example.com"
_API_KEY = "99031c76-d288-41ea-866b-ef656f58e497"


def _odoo_client(
    transport: httpx.AsyncBaseTransport,
    *,
    database: str | None = None,
    lang: str = "es_ES",
) -> OdooJson2Client:
    client = httpx.AsyncClient(base_url=_BASE, transport=transport)
    return OdooJson2Client(
        client=client,
        base_url=_BASE,
        api_key=_API_KEY,
        database=database,
        lang=lang,
    )


async def _close_odoo(odoo: OdooJson2Client) -> None:
    await odoo._client.aclose()


def test_raw_api_key_strips_bearer_prefix() -> None:
    assert raw_api_key(f"Bearer {_API_KEY}") == _API_KEY
    assert raw_api_key(f"bearer {_API_KEY}") == _API_KEY
    assert raw_api_key(_API_KEY) == _API_KEY


def test_call_posts_to_json2_endpoint() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["headers"] = dict(request.headers)
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json=[{"id": 25, "name": "Deco Addict"}])

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport)

    async def run() -> object:
        try:
            return await odoo.call(
                "res.partner",
                "search_read",
                domain=[["name", "ilike", "Deco Addict"]],
                fields=["name"],
                limit=5,
            )
        finally:
            await _close_odoo(odoo)

    result = asyncio.run(run())

    assert result == [{"id": 25, "name": "Deco Addict"}]
    assert captured["method"] == "POST"
    assert captured["path"] == "/json/2/res.partner/search_read"
    headers = captured["headers"]
    assert headers["authorization"] == f"bearer {_API_KEY}"
    assert headers["content-type"] == "application/json; charset=utf-8"
    assert headers["user-agent"] == "admin-mcp/0.1.0"
    body = captured["body"]
    assert body["domain"] == [["name", "ilike", "Deco Addict"]]
    assert body["fields"] == ["name"]
    assert body["limit"] == 5
    assert body["context"] == {"lang": "es_ES"}


def test_call_with_database_sends_header() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json=42)

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport, database="mi_db")

    async def run() -> None:
        try:
            await odoo.call("sale.order", "create", vals_list=[{"partner_id": 25}])
        finally:
            await _close_odoo(odoo)

    asyncio.run(run())

    headers = captured["headers"]
    assert headers["x-odoo-database"] == "mi_db"


def test_call_preserves_explicit_context() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode())
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport)

    async def run() -> None:
        try:
            await odoo.call(
                "res.partner",
                "search_read",
                context={"lang": "en_US", "tz": "Europe/Madrid"},
            )
        finally:
            await _close_odoo(odoo)

    asyncio.run(run())

    body = captured["body"]
    assert body["context"] == {"lang": "en_US", "tz": "Europe/Madrid"}


@pytest.mark.parametrize(
    ("status_code", "error_cls"),
    [
        (401, UnauthorizedError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (422, ValidationApiError),
    ],
)
def test_call_maps_http_errors(status_code: int, error_cls: type[AppApiError]) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            json={
                "name": "odoo.exceptions.AccessError",
                "message": "Access denied",
                "arguments": [],
                "context": {},
                "debug": "",
            },
        )

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport)

    async def run() -> None:
        try:
            with pytest.raises(error_cls) as exc_info:
                await odoo.call("res.partner", "search_read")
            assert exc_info.value.status_code == status_code
            assert exc_info.value.body is not None
            assert exc_info.value.body["message"] == "Access denied"
            assert str(exc_info.value) == "Access denied"
        finally:
            await _close_odoo(odoo)

    asyncio.run(run())


def test_call_maps_unknown_error_to_app_api_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "Internal error"})

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport)

    async def run() -> None:
        try:
            with pytest.raises(AppApiError) as exc_info:
                await odoo.call("res.partner", "search_read")
            assert exc_info.value.status_code == 500
            assert str(exc_info.value) == "Internal error"
        finally:
            await _close_odoo(odoo)

    asyncio.run(run())


def test_healthcheck_gets_version_without_auth() -> None:
    captured: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["headers"] = dict(request.headers)
        return httpx.Response(
            200,
            json={"server_version": "19.0", "server_version_info": [19, 0, 0, "final", 0]},
        )

    transport = httpx.MockTransport(handler)
    odoo = _odoo_client(transport)

    async def run() -> object:
        try:
            return await odoo.healthcheck()
        finally:
            await _close_odoo(odoo)

    result = asyncio.run(run())

    assert result["server_version"] == "19.0"
    assert captured["method"] == "GET"
    assert captured["path"] == "/web/version"
    headers = captured["headers"]
    assert "authorization" not in headers
