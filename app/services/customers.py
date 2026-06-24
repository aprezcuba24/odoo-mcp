"""Búsqueda de clientes Odoo (res.partner)."""

from __future__ import annotations

from typing import Any

from app.clients.odoo_json2 import OdooJson2Client
from app.utils.odoo_domain import OdooDomainBuilder, OdooOperator
from app.utils.object_response import ListResponse, Normalizer, ObjectResponse

MAX_LIMIT = 20


class CustomerSearchDomain(OdooDomainBuilder):
    base_filters = ["|", ["customer_rank", OdooOperator.GT, 0], ["order_bridge_registered", OdooOperator.EQ, True]]
    query = [
        "|",
        "|",
        ["name", OdooOperator.EQ],
        ["vat", OdooOperator.ILIKE],
        ["email", OdooOperator.ILIKE],
    ]


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
    name: str | None = None,
    vat: str | None = None,
    email: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search via ``res.partner.search_read``."""
    builder = CustomerSearchDomain(name=name, vat=vat, email=email)
    domain = builder.build_domain()
    has_criteria = any(value for value in (name, vat, email))

    partners = await odoo.call(
        "res.partner",
        "search_read",
        domain=domain,
        fields=["id", "name", "email", "phone", "vat"],
        limit=min(limit, MAX_LIMIT),
    )

    message: str | None = None
    if not partners:
        if not has_criteria:
            message = "No hay contactos registrados."
        else:
            message = "No hay clientes que coincidan con el criterio indicado."

    return _customer_list.build(
        partners,
        message=message,
    )
