"""Unit tests for shop-key encode/decode (offline, no HTTP)."""

from __future__ import annotations

import base64
import re

import pytest

from app.utils.exceptions import InvalidShopKeyError
from app.utils.shop_key_codec import (
    SHOP_KEY_BEARER_PREFIX,
    encode_shop_key,
    encode_shop_key_from_credentials,
    shop_context_from_encoded,
)

_TOKEN = "99031c76-d288-41ea-866b-ef656f58e497"
_BASE = "https://admin.example.com"
_INVALID_MSG = re.escape("Invalid shop-key: expected base64(BASE_URL|user_token).")


def test_encode_decode_roundtrip() -> None:
    raw = encode_shop_key(_BASE, _TOKEN)
    b64 = raw.removeprefix(SHOP_KEY_BEARER_PREFIX)
    assert raw.startswith(SHOP_KEY_BEARER_PREFIX)

    ctx = shop_context_from_encoded(raw)
    assert ctx.storage_key == b64
    assert ctx.base_url == _BASE
    assert ctx.bearer_token == f"Bearer {_TOKEN}"


def test_encode_from_credentials() -> None:
    raw = encode_shop_key_from_credentials(f"{_BASE}|{_TOKEN}")
    ctx = shop_context_from_encoded(raw)
    assert ctx.bearer_token == f"Bearer {_TOKEN}"


def test_encode_strips_trailing_slash_from_url() -> None:
    raw = encode_shop_key("http://localhost:8069/", "token")
    ctx = shop_context_from_encoded(raw)
    assert ctx.base_url == "http://localhost:8069"


def test_decode_accepts_bare_base64() -> None:
    b64 = base64.b64encode(f"{_BASE}|{_TOKEN}".encode()).decode()
    ctx = shop_context_from_encoded(b64)
    assert ctx.storage_key == b64
    assert ctx.base_url == _BASE


def test_decode_invalid_base64_raises() -> None:
    with pytest.raises(InvalidShopKeyError, match=_INVALID_MSG):
        shop_context_from_encoded("Bearer not-valid-base64!!!")


def test_decode_missing_pipe_raises() -> None:
    payload = base64.b64encode(b"https://example.com").decode()
    with pytest.raises(InvalidShopKeyError, match=_INVALID_MSG):
        shop_context_from_encoded(f"Bearer {payload}")


def test_decode_empty_parts_raises() -> None:
    payload = base64.b64encode(b"|token").decode()
    with pytest.raises(InvalidShopKeyError, match=_INVALID_MSG):
        shop_context_from_encoded(f"Bearer {payload}")

    payload = base64.b64encode(b"https://x.com|").decode()
    with pytest.raises(InvalidShopKeyError, match=_INVALID_MSG):
        shop_context_from_encoded(f"Bearer {payload}")


def test_different_backends_same_token_different_storage_keys() -> None:
    key_a = encode_shop_key("https://a.example.com", _TOKEN)
    key_b = encode_shop_key("https://b.example.com", _TOKEN)
    assert key_a != key_b
