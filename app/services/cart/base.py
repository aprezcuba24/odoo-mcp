"""Cart store protocol and shared types."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class CartStoreKey:
    """Cart partition: backend domain (netloc) + API user token."""

    backend: str
    token: str


@dataclass(frozen=True, slots=True)
class CartLine:
    product_id: int
    qty: float


@dataclass(frozen=True, slots=True)
class AdminCart:
    partner_id: int | None
    partner_name: str | None
    lines: list[CartLine]


def normalize_lines(lines: dict[int, float]) -> list[CartLine]:
    return [
        CartLine(product_id=product_id, qty=qty)
        for product_id, qty in sorted(lines.items())
    ]


def empty_admin_cart() -> AdminCart:
    return AdminCart(partner_id=None, partner_name=None, lines=[])


@runtime_checkable
class CartStore(Protocol):
    async def set_partner(
        self,
        key: CartStoreKey,
        *,
        partner_id: int,
        partner_name: str,
    ) -> AdminCart: ...

    async def add_lines(
        self,
        key: CartStoreKey,
        lines: list[tuple[int, float]],
    ) -> AdminCart: ...

    async def get_cart(self, key: CartStoreKey) -> AdminCart: ...

    async def clear(self, key: CartStoreKey) -> None: ...
