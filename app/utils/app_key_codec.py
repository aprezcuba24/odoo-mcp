"""Encode/decode auth-key: header (Bearer base64) or query param key (base64)."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

from app.clients.odoo_json2 import raw_api_key
from app.services.cart.base import CartStoreKey
from app.utils.exceptions import (
    AmbiguousAuthKeyError,
    InvalidAuthKeyError,
    MissingAuthKeyError,
)

APP_KEY_HEADER = "auth-key"
APP_KEY_QUERY_PARAM = "key"
APP_KEY_BEARER_PREFIX = "Bearer "
APP_CONTEXT_STATE_KEY = "app_context"

_BEARER_RE = re.compile(r"^Bearer\s+(\S+)\s*$", re.IGNORECASE)
_INVALID_AUTH_KEY_MSG = "Invalid auth-key: expected base64(BASE_URL|API_KEY[|database])."


@dataclass(frozen=True, slots=True)
class AppContext:
    """Decoded auth-key: backend URL, API key, optional database, and base64 credential."""

    storage_key: str
    base_url: str
    bearer_token: str
    user_token: str
    database: str | None

    def cart_store_key(self) -> CartStoreKey:
        return CartStoreKey(
            backend=backend_domain(self.base_url),
            token=raw_api_key(self.user_token),
        )


def backend_domain(base_url: str) -> str:
    """Extract host (netloc) from base_url without scheme (e.g. https://)."""
    url = base_url if "://" in base_url else f"//{base_url}"
    netloc = urlparse(url).netloc
    return netloc or base_url.strip("/")


def encode_app_key(
    base_url: str,
    user_token: str,
    database: str | None = None,
) -> str:
    """Build auth-key: ``Bearer`` + base64(``BASE_URL|API_KEY[|database]``)."""
    payload = f"{base_url.rstrip('/')}|{user_token}"
    if database:
        payload = f"{payload}|{database}"
    b64 = base64.b64encode(payload.encode()).decode()
    return f"{APP_KEY_BEARER_PREFIX}{b64}"


def encode_app_key_from_credentials(credentials: str) -> str:
    """Encode ``BASE_URL|API_KEY[|database]`` into a full auth-key header value."""
    parts = credentials.split("|", 2)
    if len(parts) < 2:
        raise InvalidAuthKeyError(_INVALID_AUTH_KEY_MSG)
    base_url = parts[0].rstrip("/")
    api_key = parts[1].strip()
    database = parts[2].strip() if len(parts) == 3 and parts[2].strip() else None
    return encode_app_key(base_url, api_key, database)


def _strip_bearer(value: str) -> str:
    match = _BEARER_RE.match(value.strip())
    return match.group(1) if match else value.strip()


def _parse_credentials_payload(decoded: str) -> tuple[str, str, str | None]:
    parts = decoded.split("|", 2)
    if len(parts) < 2:
        raise InvalidAuthKeyError(_INVALID_AUTH_KEY_MSG)

    base_url = parts[0].rstrip("/")
    user_token = parts[1].strip()
    database = parts[2].strip() if len(parts) == 3 and parts[2].strip() else None
    if not base_url or not user_token:
        raise InvalidAuthKeyError(_INVALID_AUTH_KEY_MSG)
    return base_url, user_token, database


def _app_context_from_b64(b64: str) -> AppContext:
    try:
        decoded = base64.b64decode(b64, validate=True).decode()
    except Exception as exc:
        raise InvalidAuthKeyError(_INVALID_AUTH_KEY_MSG) from exc

    base_url, user_token, database = _parse_credentials_payload(decoded)

    bearer_token = (
        user_token
        if user_token.lower().startswith("bearer ")
        else f"Bearer {user_token}"
    )

    return AppContext(
        storage_key=b64,
        base_url=base_url,
        bearer_token=bearer_token,
        user_token=user_token,
        database=database,
    )


def app_context_from_encoded(raw: str) -> AppContext:
    """Decode auth-key string offline (CLI/tests); no HTTP validation."""
    return _app_context_from_b64(_strip_bearer(raw))


def parse_app_key(request: Request) -> AppContext:
    """Extract, validate and decode auth-key from an HTTP request."""
    header = (request.headers.get(APP_KEY_HEADER) or "").strip() or ""
    header = _strip_bearer(header)
    query = (request.query_params.get(APP_KEY_QUERY_PARAM) or "").strip() or None

    if header and query:
        raise AmbiguousAuthKeyError()
    if not header and not query:
        raise MissingAuthKeyError()

    return _app_context_from_b64(header or query)


def resolve_app_context() -> AppContext:
    """Return auth-key context set by AppKeyMiddleware on the current request."""
    request = get_http_request()
    ctx = getattr(request.state, APP_CONTEXT_STATE_KEY, None)
    if ctx is None:
        raise RuntimeError("App context not set; AppKeyMiddleware required.")
    return ctx


def resolve_app_key() -> str:
    """Base64 auth-key credential from the current request."""
    return resolve_app_context().storage_key
