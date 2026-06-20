"""FastMCP server: Streamable HTTP + HTTP client lifespan."""

from __future__ import annotations

from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from app.config import get_settings
from .app_state import ClientRegistry, app_state
from .instructions import instructions
from .middleware import MCP_HTTP_MIDDLEWARE


@lifespan
async def app_lifespan(server: FastMCP):
    settings = get_settings()
    registry = ClientRegistry(timeout=settings.admin_api_timeout)
    app_state.registry = registry
    try:
        yield {"settings": settings}
    finally:
        await registry.close_all()
        app_state.registry = None


mcp = FastMCP(
    name="admin-mcp",
    version="0.1.0",
    instructions=instructions,
    lifespan=app_lifespan,
)


def run() -> None:
    settings = get_settings()
    mcp.run(
        transport="streamable-http",
        host=settings.mcp_host,
        port=settings.mcp_port,
        path=settings.mcp_path,
        middleware=MCP_HTTP_MIDDLEWARE,
    )
