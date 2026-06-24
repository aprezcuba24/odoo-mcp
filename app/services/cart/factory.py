"""Cart store factory (memory in dev, DynamoDB in production)."""

from __future__ import annotations

from app.config import Settings, get_settings
from app.services.cart.base import CartStore
from app.services.cart.dynamodb import DynamoDBCartStore
from app.services.cart.memory import InMemoryCartStore


def create_cart_store(settings: Settings | None = None) -> CartStore:
    settings = settings or get_settings()
    if settings.cart_store_backend == "dynamodb":
        return DynamoDBCartStore(table_name=settings.dynamodb_cart_table)
    return InMemoryCartStore()
