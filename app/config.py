"""Application settings (environment / .env)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    admin_api_timeout: float = Field(default=30.0, ge=1.0)
    cart_store_backend: Literal["memory", "dynamodb"] = "memory"
    dynamodb_cart_table: str = "admin-mcp-cart"
    mcp_host: str = Field(default="0.0.0.0")
    mcp_port: int = Field(default=8001, ge=1, le=65535)
    mcp_path: str = Field(default="/mcp")


def get_settings() -> Settings:
    return Settings()
