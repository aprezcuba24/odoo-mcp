"""Búsqueda de clientes Odoo (res.partner)."""

from __future__ import annotations

from typing import Any

from app.clients.odoo_json2 import OdooJson2Client
from app.utils.object_response import ListResponse, Normalizer, ObjectResponse

MAX_LIMIT = 20


class PartnerResponse(ObjectResponse):
    id = Normalizer.RAW
    name = Normalizer.DEFAULT_EMPTY
    phone = Normalizer.OPTIONAL
    order_bridge_registered = Normalizer.RAW
    order_bridge_phone_validated = Normalizer.RAW
    address = Normalizer.RAW


_customer_list = ListResponse(PartnerResponse(), items_key="customers")

_CUSTOMER_DISPLAY_FIELDS = ["id", "name", "phone", "address"]

_DISAMBIGUATE_HINT = (
    "Lista candidatos numerados con id visible; "
    "espera elección del usuario (suele indicar el id)."
)


def _customer_agent_hint(count: int) -> dict[str, Any]:
    if count == 0:
        return {"next": "ask_user_for_different_criteria"}
    if count > 1:
        return {
            "next": "disambiguate",
            "display": _CUSTOMER_DISPLAY_FIELDS,
            "hint": _DISAMBIGUATE_HINT,
        }
    return {"next": "confirm_or_proceed"}


async def search_customers(
    odoo: OdooJson2Client,
    *,
    query: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search via ``res.partner.api_search_customers`` (nombre, teléfono y dirección)."""
    params: dict[str, Any] = {"limit": min(limit, MAX_LIMIT)}
    if query is not None and str(query).strip():
        params["query"] = str(query).strip()

    partners = await odoo.call("res.partner", "api_search_customers", **params)

    message: str | None = None
    if not partners:
        if not query:
            message = "No hay contactos registrados."
        else:
            message = "No hay clientes que coincidan con el criterio indicado."

    result = _customer_list.build(
        partners,
        message=message,
    )
    result["_agent"] = _customer_agent_hint(result["count"])
    return result
