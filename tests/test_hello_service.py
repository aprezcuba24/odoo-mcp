"""Unit tests for hello world service."""

from __future__ import annotations

from app.services.hello import build_hello_payload
from app.utils.app_key_codec import AppContext

_CTX = AppContext(
    storage_key="abc",
    base_url="http://localhost:8069",
    bearer_token="Bearer token",
    user_token="token",
    database=None,
)


def test_build_hello_payload_default() -> None:
    payload = build_hello_payload(_CTX)
    assert payload["message"] == "Hola, mundo!"
    assert payload["name"] is None
    assert payload["backend"] == "http://localhost:8069"


def test_build_hello_payload_with_name() -> None:
    payload = build_hello_payload(_CTX, name="Ana")
    assert payload["message"] == "Hola, Ana!"
    assert payload["name"] == "Ana"
    assert payload["backend"] == "http://localhost:8069"
