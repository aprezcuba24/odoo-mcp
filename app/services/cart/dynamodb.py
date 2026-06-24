"""DynamoDB-backed admin cart store (production / Lambda)."""

from __future__ import annotations

import asyncio
from decimal import Decimal
from typing import Any

from app.services.cart.base import AdminCart, CartStoreKey, empty_admin_cart, normalize_lines


def _lines_to_dynamo(lines: dict[int, float]) -> dict[str, dict[str, str]]:
    return {str(product_id): {"N": str(qty)} for product_id, qty in lines.items()}


def _dynamo_number(value: Any) -> float:
    if isinstance(value, dict):
        if "N" in value:
            return float(value["N"])
        if "S" in value:
            return float(value["S"])
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _lines_from_dynamo(raw: dict[str, Any] | None) -> dict[int, float]:
    if not raw:
        return {}
    result: dict[int, float] = {}
    for product_id, qty in raw.items():
        result[int(product_id)] = _dynamo_number(qty)
    return result


def _item_key(key: CartStoreKey) -> dict[str, dict[str, str]]:
    return {"backend": {"S": key.backend}, "token": {"S": key.token}}


class DynamoDBCartStore:
    """Cart persistence in DynamoDB (PK=backend domain, SK=token)."""

    __slots__ = ("_client", "_table_name")

    def __init__(self, table_name: str, *, client: Any | None = None) -> None:
        if client is None:
            import boto3

            client = boto3.client("dynamodb")
        self._client = client
        self._table_name = table_name

    async def set_partner(
        self,
        key: CartStoreKey,
        *,
        partner_id: int,
        partner_name: str,
    ) -> AdminCart:
        state = await self._get_raw_state(key)
        if state["partner_id"] is not None:
            raise ValueError(
                "Ya hay un carrito activo con un cliente asignado. "
                "Confirma el pedido con create_order o vacía el carrito con clear_cart "
                "antes de seleccionar otro cliente."
            )
        state["partner_id"] = partner_id
        state["partner_name"] = partner_name
        await asyncio.to_thread(self._put_state, key, state)
        return self._to_admin_cart(state)

    async def add_lines(
        self,
        key: CartStoreKey,
        lines: list[tuple[int, float]],
    ) -> AdminCart:
        if not lines:
            raise ValueError("Debe indicar al menos una línea de producto.")

        state = await self._get_raw_state(key)
        if state["partner_id"] is None:
            raise ValueError(
                "No hay cliente en el carrito. "
                "Llama primero a create_cart con el partner_id del cliente."
            )
        for product_id, quantity in lines:
            if quantity <= 0:
                raise ValueError("quantity must be greater than 0.")
            state["lines"][product_id] = state["lines"].get(product_id, 0.0) + quantity
        await asyncio.to_thread(self._put_state, key, state)
        return self._to_admin_cart(state)

    async def get_cart(self, key: CartStoreKey) -> AdminCart:
        state = await self._get_raw_state(key)
        return self._to_admin_cart(state)

    async def clear(self, key: CartStoreKey) -> None:
        await asyncio.to_thread(
            self._client.delete_item,
            TableName=self._table_name,
            Key=_item_key(key),
        )

    async def _get_raw_state(self, key: CartStoreKey) -> dict[str, Any]:
        response = await asyncio.to_thread(
            self._client.get_item,
            TableName=self._table_name,
            Key=_item_key(key),
        )
        item = response.get("Item")
        if not item:
            return {"partner_id": None, "partner_name": None, "lines": {}}
        partner_id_raw = item.get("partner_id", {}).get("N")
        partner_name = item.get("partner_name", {}).get("S")
        raw_lines = item.get("lines", {}).get("M")
        return {
            "partner_id": int(partner_id_raw) if partner_id_raw else None,
            "partner_name": partner_name,
            "lines": _lines_from_dynamo(raw_lines),
        }

    def _put_state(self, key: CartStoreKey, state: dict[str, Any]) -> None:
        item: dict[str, Any] = {
            "backend": {"S": key.backend},
            "token": {"S": key.token},
            "lines": {"M": _lines_to_dynamo(state["lines"])},
        }
        if state["partner_id"] is not None:
            item["partner_id"] = {"N": str(state["partner_id"])}
        if state["partner_name"]:
            item["partner_name"] = {"S": state["partner_name"]}
        self._client.put_item(TableName=self._table_name, Item=item)

    @staticmethod
    def _to_admin_cart(state: dict[str, Any]) -> AdminCart:
        if state["partner_id"] is None:
            return empty_admin_cart()
        return AdminCart(
            partner_id=state["partner_id"],
            partner_name=state["partner_name"],
            lines=normalize_lines(state["lines"]),
        )
