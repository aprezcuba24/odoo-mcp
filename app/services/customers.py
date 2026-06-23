"""Búsqueda de clientes Odoo (res.partner)."""

from __future__ import annotations

from typing import Any, Literal

from app.clients.odoo_json2 import OdooJson2Client

CUSTOMER_FILTER: list[Any] = ["customer_rank", ">", 0]
FIELDS = ["id", "name", "email", "phone", "vat"]
MAX_LIMIT = 20

SearchMode = Literal["name", "vat", "email", "query"]
IDENTIFIER_MODES: frozenset[SearchMode] = frozenset({"name", "vat", "email"})


def _resolve_search_mode(
    *,
    query: str | None,
    name: str | None,
    vat: str | None,
    email: str | None,
) -> tuple[SearchMode, str] | None:
    if name:
        return "name", name
    if vat:
        return "vat", vat
    if email:
        return "email", email
    if query:
        return "query", query
    return None


def _build_domain(mode: SearchMode, value: str) -> list[list[Any]]:
    if mode == "name":
        criterion: list[Any] = ["name", "=", value]
    elif mode == "vat":
        criterion = ["vat", "ilike", value]
    elif mode == "email":
        criterion = ["email", "ilike", value]
    else:
        criterion = ["name", "ilike", value]
    return [criterion, CUSTOMER_FILTER]


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
    resolved = _resolve_search_mode(query=query, name=name, vat=vat, email=email)
    if resolved is None:
        return _empty_response(
            message="Indica al menos un criterio: query, name, vat o email.",
        )

    mode, value = resolved
    domain = _build_domain(mode, value)
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
