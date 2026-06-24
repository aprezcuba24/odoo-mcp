"""Búsqueda de clientes Odoo (res.partner)."""

from __future__ import annotations

from typing import Any

from app.clients.odoo_json2 import OdooJson2Client
from app.utils.odoo_domain import OdooDomainBuilder, OdooOperator
from app.utils.object_response import ListResponse, Normalizer, ObjectResponse

MAX_LIMIT = 20


class CustomerSearchDomain(OdooDomainBuilder):
    name = OdooOperator.EQ
    vat = OdooOperator.ILIKE
    email = OdooOperator.ILIKE
    query = OdooOperator.ILIKE

    priority = ("name", "vat", "email", "query")
    odoo_fields = {"query": "name"}
    base_filters = ["|", ["customer_rank", ">", 0], ["order_bridge_registered", "=", True]]


class PartnerResponse(ObjectResponse):
    id = Normalizer.RAW
    name = Normalizer.DEFAULT_EMPTY
    email = Normalizer.OPTIONAL
    phone = Normalizer.OPTIONAL
    vat = Normalizer.OPTIONAL


_customer_list = ListResponse(PartnerResponse(), items_key="customers")


async def search_customers(
    odoo: OdooJson2Client,
    *,
    query: str | None = None,
    name: str | None = None,
    vat: str | None = None,
    email: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search via ``res.partner.search_read``."""
    builder = CustomerSearchDomain(query=query, name=name, vat=vat, email=email)
    resolved = builder.resolve_criterion()
    domain = builder.build_domain()
    search_meta = None if resolved is None else {"mode": resolved[0], "value": resolved[1]}

    partners = await odoo.call(
        "res.partner",
        "search_read",
        domain=domain,
        fields=["id", "name", "email", "phone", "vat"],
        limit=min(limit, MAX_LIMIT),
    )

    message: str | None = None
    if not partners:
        if resolved is None:
            message = "No hay contactos registrados."
        else:
            message = "No hay clientes que coincidan con el criterio indicado."

    return _customer_list.build(
        partners,
        search=search_meta,
        message=message,
    )
