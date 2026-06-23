"""Construcción reutilizable de domains Odoo."""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar


class OdooOperator(str, Enum):
    EQ = "="
    ILIKE = "ilike"
    GT = ">"


class OdooDomainBuilder:
    """Base para builders de domain con operadores declarados por atributo de clase."""

    priority: ClassVar[tuple[str, ...]] = ()
    odoo_fields: ClassVar[dict[str, str]] = {}
    base_filters: ClassVar[list[list[Any]]] = []

    def __init__(self, **kwargs: str | None) -> None:
        self._values = kwargs

    def resolve_criterion(self) -> tuple[str, str] | None:
        for param in type(self).priority:
            value = self._values.get(param)
            if value:
                return param, value
        return None

    def build_domain(self) -> list[list[Any]] | None:
        resolved = self.resolve_criterion()
        if resolved is None:
            return None
        param, value = resolved
        operator = getattr(type(self), param)
        odoo_field = type(self).odoo_fields.get(param, param)
        domain: list[list[Any]] = [[odoo_field, operator.value, value]]
        domain.extend(type(self).base_filters)
        return domain
