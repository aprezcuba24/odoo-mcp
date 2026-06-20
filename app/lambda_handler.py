"""AWS Lambda entrypoint (Mangum + FastMCP Streamable HTTP)."""

from __future__ import annotations

from mangum import Mangum

from app.config import get_settings
from app.server import mcp
from app.server.middleware import MCP_HTTP_MIDDLEWARE

settings = get_settings()
app = mcp.http_app(
    path=settings.mcp_path,
    transport="streamable-http",
    stateless_http=True,
    middleware=MCP_HTTP_MIDDLEWARE,
)
handler = Mangum(app, lifespan="auto")
