"""Búsqueda de clientes Odoo (res.partner)."""

from __future__ import annotations

from typing import Any, Literal

from app.clients.odoo_json2 import OdooJson2Client
from app.utils.odoo_domain import OdooDomainBuilder, OdooOperator

CUSTOMER_FILTER: list[Any] = ["customer_rank", ">", 0]
FIELDS = ["id", "name", "email", "phone", "vat"]
MAX_LIMIT = 20

SearchMode = Literal["name", "vat", "email", "query"]
IDENTIFIER_MODES: frozenset[SearchMode] = frozenset({"name", "vat", "email"})


class CustomerSearchDomain(OdooDomainBuilder):
    name = OdooOperator.EQ
    vat = OdooOperator.ILIKE
    email = OdooOperator.ILIKE
    query = OdooOperator.ILIKE

    priority = ("name", "vat", "email", "query")
    odoo_fields = {"query": "name"}
    base_filters = [CUSTOMER_FILTER]


def _effective_limit(mode: SearchMode, limit: int) -> int:
    if mode == "name":
        return 2
    return min(limit, MAX_LIMIT)


def _normalize_optional(value: Any) -> str | None:
    if value is False or value is None:
        return None
    return str(value)


def _normalize_partner(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record["id"],
        "name": record.get("name") or "",
        "email": _normalize_optional(record.get("email")),
        "phone": _normalize_optional(record.get("phone")),
        "vat": _normalize_optional(record.get("vat")),
    }


def _empty_response(*, message: str) -> dict[str, Any]:
    return {
        "count": 0,
        "ambiguous": False,
        "customers": [],
        "search": None,
        "message": message,
    }


async def search_customers(
    odoo: OdooJson2Client,
    *,
    query: str | None = None,
    name: str | None = None,
    vat: str | None = None,
    email: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search customers via ``res.partner.search_read`` (customers only)."""
    builder = CustomerSearchDomain(query=query, name=name, vat=vat, email=email)
    resolved = builder.resolve_criterion()
    if resolved is None:
        return _empty_response(
            message="Indica al menos un criterio: query, name, vat o email.",
        )

    mode, value = resolved
    domain = builder.build_domain()
    effective_limit = _effective_limit(mode, limit)

    partners = await odoo.call(
        "res.partner",
        "search_read",
        domain=domain,
        fields=FIELDS,
        limit=effective_limit,
    )

    customers = [_normalize_partner(record) for record in partners]
    count = len(customers)
    ambiguous = mode in IDENTIFIER_MODES and count > 1

    message: str | None = None
    if count == 0:
        message = "No hay clientes que coincidan con el criterio indicado."

    return {
        "count": count,
        "ambiguous": ambiguous,
        "customers": customers,
        "search": {"mode": mode, "value": value},
        "message": message,
    }
