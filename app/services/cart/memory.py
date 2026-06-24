"""In-memory admin cart (development)."""

from __future__ import annotations

import asyncio

from app.services.cart.base import AdminCart, CartStoreKey, empty_admin_cart, normalize_lines


def _storage_key(key: CartStoreKey) -> str:
    return f"{key.backend}\0{key.token}"


class _CartState:
    __slots__ = ("partner_id", "partner_name", "lines")

    def __init__(self) -> None:
        self.partner_id: int | None = None
        self.partner_name: str | None = None
        self.lines: dict[int, float] = {}

    def to_admin_cart(self) -> AdminCart:
        if self.partner_id is None:
            return empty_admin_cart()
        return AdminCart(
            partner_id=self.partner_id,
            partner_name=self.partner_name,
            lines=normalize_lines(self.lines),
        )


class InMemoryCartStore:
    """Per-process cart storage keyed by backend domain + token."""

    __slots__ = ("_carts", "_lock")

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._carts: dict[str, _CartState] = {}

    async def set_partner(
        self,
        key: CartStoreKey,
        *,
        partner_id: int,
        partner_name: str,
    ) -> AdminCart:
        storage_key = _storage_key(key)
        async with self._lock:
            state = self._carts.get(storage_key)
            if state is not None and state.partner_id is not None:
                raise ValueError(
                    "Ya hay un carrito activo con un cliente asignado. "
                    "Confirma el pedido con create_order o vacía el carrito con clear_cart "
                    "antes de seleccionar otro cliente."
                )
            if state is None:
                state = _CartState()
                self._carts[storage_key] = state
            state.partner_id = partner_id
            state.partner_name = partner_name
            return state.to_admin_cart()

    async def add_lines(
        self,
        key: CartStoreKey,
        lines: list[tuple[int, float]],
    ) -> AdminCart:
        if not lines:
            raise ValueError("Debe indicar al menos una línea de producto.")

        storage_key = _storage_key(key)
        async with self._lock:
            state = self._carts.get(storage_key)
            if state is None or state.partner_id is None:
                raise ValueError(
                    "No hay cliente en el carrito. "
                    "Llama primero a create_cart con el partner_id del cliente."
                )
            for product_id, quantity in lines:
                if quantity <= 0:
                    raise ValueError("quantity must be greater than 0.")
                state.lines[product_id] = state.lines.get(product_id, 0.0) + quantity
            return state.to_admin_cart()

    async def get_cart(self, key: CartStoreKey) -> AdminCart:
        storage_key = _storage_key(key)
        async with self._lock:
            state = self._carts.get(storage_key)
            if state is None:
                return empty_admin_cart()
            return state.to_admin_cart()

    async def clear(self, key: CartStoreKey) -> None:
        storage_key = _storage_key(key)
        async with self._lock:
            self._carts.pop(storage_key, None)
