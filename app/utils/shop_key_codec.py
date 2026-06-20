"""Encode/decode shop-key: header (Bearer base64) or query param key (base64)."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

from app.utils.exceptions import (
    AmbiguousShopKeyError,
    InvalidShopKeyError,
    MissingShopKeyError,
)

SHOP_KEY_HEADER = "shop-key"
SHOP_KEY_QUERY_PARAM = "key"
SHOP_KEY_BEARER_PREFIX = "Bearer "
SHOP_CONTEXT_STATE_KEY = "shop_context"

_BEARER_RE = re.compile(r"^Bearer\s+(\S+)\s*$", re.IGNORECASE)
_CREDENTIALS_PAYLOAD_RE = re.compile(r"^(.+)\|(.+)$")


@dataclass(frozen=True, slots=True)
class ShopContext:
    """Decoded shop-key: backend URL, Bearer token, and base64 credential."""

    storage_key: str
    base_url: str
    bearer_token: str
    user_token: str


def backend_domain(base_url: str) -> str:
    """Extract host (netloc) from base_url without scheme (e.g. https://)."""
    url = base_url if "://" in base_url else f"//{base_url}"
    netloc = urlparse(url).netloc
    return netloc or base_url.strip("/")


def encode_shop_key(base_url: str, user_token: str) -> str:
    """Build the shop-key header value: ``Bearer`` + base64(``BASE_URL|user_token``)."""
    payload = f"{base_url.rstrip('/')}|{user_token}"
    b64 = base64.b64encode(payload.encode()).decode()
    return f"{SHOP_KEY_BEARER_PREFIX}{b64}"


def encode_shop_key_from_credentials(credentials: str) -> str:
    """Encode ``BASE_URL|user_token`` into a full shop-key header value."""
    base_url, _, user_token = credentials.partition("|")
    return encode_shop_key(base_url.rstrip("/"), user_token.strip())


def _strip_bearer(value: str) -> str:
    match = _BEARER_RE.match(value.strip())
    return match.group(1) if match else value.strip()


def _shop_context_from_b64(b64: str) -> ShopContext:
    try:
        decoded = base64.b64decode(b64, validate=True).decode()
    except Exception as exc:
        raise InvalidShopKeyError() from exc

    payload_match = _CREDENTIALS_PAYLOAD_RE.match(decoded)
    if not payload_match:
        raise InvalidShopKeyError()

    base_url = payload_match.group(1).rstrip("/")
    user_token = payload_match.group(2).strip()
    if not base_url or not user_token:
        raise InvalidShopKeyError()

    bearer_token = (
        user_token
        if user_token.lower().startswith("bearer ")
        else f"Bearer {user_token}"
    )

    return ShopContext(
        storage_key=b64,
        base_url=base_url,
        bearer_token=bearer_token,
        user_token=user_token,
    )


def shop_context_from_encoded(raw: str) -> ShopContext:
    """Decode shop-key string offline (CLI/tests); no HTTP validation."""
    return _shop_context_from_b64(_strip_bearer(raw))


def parse_shop_key(request: Request) -> ShopContext:
    """Extract, validate and decode shop-key from an HTTP request."""
    header = (request.headers.get(SHOP_KEY_HEADER) or "").strip() or ""
    header = _strip_bearer(header)
    query = (request.query_params.get(SHOP_KEY_QUERY_PARAM) or "").strip() or None

    if header and query:
        raise AmbiguousShopKeyError()
    if not header and not query:
        raise MissingShopKeyError()

    return _shop_context_from_b64(header or query)


def resolve_shop_context() -> ShopContext:
    """Return shop-key context set by ShopKeyMiddleware on the current request."""
    request = get_http_request()
    ctx = getattr(request.state, SHOP_CONTEXT_STATE_KEY, None)
    if ctx is None:
        raise RuntimeError("Shop context not set; ShopKeyMiddleware required.")
    return ctx


def resolve_shop_key() -> str:
    """Base64 shop-key credential from the current request."""
    return resolve_shop_context().storage_key
