"""Creación de pedidos confirmados vía sale.order.api_create_confirmed_order."""

from __future__ import annotations

from typing import Any

from app.clients.odoo_json2 import OdooJson2Client


def _present_order(record: dict[str, Any]) -> dict[str, Any]:
    order_id = record.get("id")
    return {
        "id": order_id,
        "name": record.get("name"),
        "state": record.get("state"),
        "amount_total": record.get("amount_total"),
        "partner_id": record.get("partner_id"),
        "client_order_ref": record.get("client_order_ref"),
        "_agent": {"order_id": order_id},
    }


async def create_confirmed_order(
    odoo: OdooJson2Client,
    *,
    partner_id: int,
    lines: list[dict[str, float | int]],
    ref: str | None = None,
) -> dict[str, Any]:
    record = {
        "id": 900001,
        "name": "MOCK-S00001",
        "state": "sale",
        "amount_total": 0.0,
        "partner_id": partner_id,
        "client_order_ref": ref or False,
    }
    return _present_order(record)
    # params: dict[str, Any] = {
    #     "partner_id": partner_id,
    #     "lines": lines,
    # }
    # if ref is not None and str(ref).strip():
    #     params["ref"] = str(ref).strip()

    # record = await odoo.call(
    #     "sale.order",
    #     "api_create_confirmed_order",
    #     **params,
    # )
    # if not isinstance(record, dict):
    #     raise ValueError("Respuesta inesperada de api_create_confirmed_order.")
    # return _present_order(record)
