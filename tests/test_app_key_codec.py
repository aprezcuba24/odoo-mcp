"""Unit tests for auth-key encode/decode (offline, no HTTP)."""

from __future__ import annotations

import base64
import re

import pytest

from app.utils.exceptions import InvalidAuthKeyError
from app.utils.app_key_codec import (
    APP_KEY_BEARER_PREFIX,
    app_context_from_encoded,
    encode_app_key,
    encode_app_key_from_credentials,
)

_TOKEN = "99031c76-d288-41ea-866b-ef656f58e497"
_BASE = "https://admin.example.com"
_INVALID_MSG = re.escape("Invalid auth-key: expected base64(BASE_URL|API_KEY[|database]).")


def test_encode_decode_roundtrip() -> None:
    raw = encode_app_key(_BASE, _TOKEN)
    b64 = raw.removeprefix(APP_KEY_BEARER_PREFIX)
    assert raw.startswith(APP_KEY_BEARER_PREFIX)

    ctx = app_context_from_encoded(raw)
    assert ctx.storage_key == b64
    assert ctx.base_url == _BASE
    assert ctx.bearer_token == f"Bearer {_TOKEN}"
    assert ctx.database is None


def test_encode_decode_roundtrip_with_database() -> None:
    raw = encode_app_key(_BASE, _TOKEN, "mi_db")
    ctx = app_context_from_encoded(raw)
    assert ctx.base_url == _BASE
    assert ctx.bearer_token == f"Bearer {_TOKEN}"
    assert ctx.database == "mi_db"


def test_encode_from_credentials_with_database() -> None:
    raw = encode_app_key_from_credentials(f"{_BASE}|{_TOKEN}|mi_db")
    ctx = app_context_from_encoded(raw)
    assert ctx.database == "mi_db"


def test_encode_without_database_omits_third_segment() -> None:
    raw = encode_app_key(_BASE, _TOKEN)
    decoded = base64.b64decode(raw.removeprefix(APP_KEY_BEARER_PREFIX)).decode()
    assert decoded == f"{_BASE}|{_TOKEN}"
    assert decoded.count("|") == 1


def test_decode_two_segments_has_no_database() -> None:
    ctx = app_context_from_encoded(encode_app_key(_BASE, _TOKEN))
    assert ctx.database is None


def test_decode_empty_database_segment_is_none() -> None:
    payload = base64.b64encode(f"{_BASE}|{_TOKEN}|".encode()).decode()
    ctx = app_context_from_encoded(f"Bearer {payload}")
    assert ctx.database is None


def test_encode_from_credentials() -> None:
    raw = encode_app_key_from_credentials(f"{_BASE}|{_TOKEN}")
    ctx = app_context_from_encoded(raw)
    assert ctx.bearer_token == f"Bearer {_TOKEN}"


def test_encode_strips_trailing_slash_from_url() -> None:
    raw = encode_app_key("http://localhost:8069/", "token")
    ctx = app_context_from_encoded(raw)
    assert ctx.base_url == "http://localhost:8069"


def test_decode_accepts_bare_base64() -> None:
    b64 = base64.b64encode(f"{_BASE}|{_TOKEN}".encode()).decode()
    ctx = app_context_from_encoded(b64)
    assert ctx.storage_key == b64
    assert ctx.base_url == _BASE


def test_decode_invalid_base64_raises() -> None:
    with pytest.raises(InvalidAuthKeyError, match=_INVALID_MSG):
        app_context_from_encoded("Bearer not-valid-base64!!!")


def test_decode_missing_pipe_raises() -> None:
    payload = base64.b64encode(b"https://example.com").decode()
    with pytest.raises(InvalidAuthKeyError, match=_INVALID_MSG):
        app_context_from_encoded(f"Bearer {payload}")


def test_decode_empty_parts_raises() -> None:
    payload = base64.b64encode(b"|token").decode()
    with pytest.raises(InvalidAuthKeyError, match=_INVALID_MSG):
        app_context_from_encoded(f"Bearer {payload}")

    payload = base64.b64encode(b"https://x.com|").decode()
    with pytest.raises(InvalidAuthKeyError, match=_INVALID_MSG):
        app_context_from_encoded(f"Bearer {payload}")


def test_different_backends_same_token_different_storage_keys() -> None:
    key_a = encode_app_key("https://a.example.com", _TOKEN)
    key_b = encode_app_key("https://b.example.com", _TOKEN)
    assert key_a != key_b
