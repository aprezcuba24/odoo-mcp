"""Encode/decode auth-key: header (Bearer base64) or query param key (base64)."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from urllib.parse import urlparse

from fastmcp.server.dependencies import get_http_request
from starlette.requests import Request

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
_CREDENTIALS_PAYLOAD_RE = re.compile(r"^(.+)\|(.+)$")


@dataclass(frozen=True, slots=True)
class AppContext:
    """Decoded auth-key: backend URL, Bearer token, and base64 credential."""

    storage_key: str
    base_url: str
    bearer_token: str
    user_token: str


def backend_domain(base_url: str) -> str:
    """Extract host (netloc) from base_url without scheme (e.g. https://)."""
    url = base_url if "://" in base_url else f"//{base_url}"
    netloc = urlparse(url).netloc
    return netloc or base_url.strip("/")


def encode_app_key(base_url: str, user_token: str) -> str:
    """Build the auth-key header value: ``Bearer`` + base64(``BASE_URL|user_token``)."""
    payload = f"{base_url.rstrip('/')}|{user_token}"
    b64 = base64.b64encode(payload.encode()).decode()
    return f"{APP_KEY_BEARER_PREFIX}{b64}"


def encode_app_key_from_credentials(credentials: str) -> str:
    """Encode ``BASE_URL|user_token`` into a full auth-key header value."""
    base_url, _, user_token = credentials.partition("|")
    return encode_app_key(base_url.rstrip("/"), user_token.strip())


def _strip_bearer(value: str) -> str:
    match = _BEARER_RE.match(value.strip())
    return match.group(1) if match else value.strip()


def _app_context_from_b64(b64: str) -> AppContext:
    try:
        decoded = base64.b64decode(b64, validate=True).decode()
    except Exception as exc:
        raise InvalidAuthKeyError() from exc

    payload_match = _CREDENTIALS_PAYLOAD_RE.match(decoded)
    if not payload_match:
        raise InvalidAuthKeyError()

    base_url = payload_match.group(1).rstrip("/")
    user_token = payload_match.group(2).strip()
    if not base_url or not user_token:
        raise InvalidAuthKeyError()

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
