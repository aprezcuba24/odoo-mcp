"""Unit tests for auth-key HTTP middleware."""

from __future__ import annotations

import base64

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.responses import PlainTextResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.server.app_key_middleware import AppKeyMiddleware
from app.utils.app_key_codec import (
    APP_CONTEXT_STATE_KEY,
    APP_KEY_BEARER_PREFIX,
    encode_app_key,
)

_BASE = "http://localhost:8069"
_USER_TOKEN = "99031c76-d288-41ea-866b-ef656f58e497"
_ENCODED = encode_app_key(_BASE, _USER_TOKEN)
_B64_ONLY = _ENCODED.removeprefix(APP_KEY_BEARER_PREFIX)


async def _read_context(request):
    ctx = getattr(request.state, APP_CONTEXT_STATE_KEY)
    return PlainTextResponse(f"{ctx.base_url}|{ctx.user_token}")


def _client() -> TestClient:
    app = Starlette(
        routes=[Route("/mcp", _read_context, methods=["POST"])],
        middleware=[Middleware(AppKeyMiddleware)],
    )
    return TestClient(app)


def test_middleware_rejects_header_and_query_together() -> None:
    with _client() as client:
        response = client.post(
            f"/mcp?key={_B64_ONLY}",
            headers={"auth-key": _ENCODED},
        )

    assert response.status_code == 400
    assert "Ambiguous auth-key" in response.json()["error"]


def test_middleware_rejects_missing_auth_key() -> None:
    with _client() as client:
        response = client.post("/mcp")

    assert response.status_code == 401
    assert "Missing auth-key" in response.json()["error"]


def test_middleware_rejects_invalid_auth_key() -> None:
    with _client() as client:
        response = client.post("/mcp", headers={"auth-key": "Bearer not-valid!!!"})

    assert response.status_code == 400
    assert "Invalid auth-key" in response.json()["error"]


def test_middleware_rejects_missing_pipe_in_payload() -> None:
    payload = base64.b64encode(b"https://example.com").decode()
    with _client() as client:
        response = client.post("/mcp", headers={"auth-key": f"Bearer {payload}"})

    assert response.status_code == 400
    assert "Invalid auth-key" in response.json()["error"]


def test_middleware_rejects_empty_payload_parts() -> None:
    payload = base64.b64encode(b"|token").decode()
    with _client() as client:
        response = client.post("/mcp", headers={"auth-key": f"Bearer {payload}"})

    assert response.status_code == 400
    assert "Invalid auth-key" in response.json()["error"]

    payload = base64.b64encode(b"https://x.com|").decode()
    with _client() as client:
        response = client.post("/mcp", headers={"auth-key": f"Bearer {payload}"})

    assert response.status_code == 400
    assert "Invalid auth-key" in response.json()["error"]


def test_middleware_attaches_context_from_header() -> None:
    with _client() as client:
        response = client.post("/mcp", headers={"auth-key": _ENCODED})

    assert response.status_code == 200
    assert response.text == f"{_BASE}|{_USER_TOKEN}"


def test_middleware_attaches_context_from_query() -> None:
    with _client() as client:
        response = client.post(f"/mcp?key={_B64_ONLY}")

    assert response.status_code == 200
    assert response.text == f"{_BASE}|{_USER_TOKEN}"
