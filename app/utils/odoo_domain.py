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
    base_filters: ClassVar[list[list[Any]] | None] = None

    def __init__(
        self,
        *,
        base_filters: list[list[Any]] | None = None,
        **kwargs: str | None,
    ) -> None:
        self._values = kwargs
        if base_filters is not None:
            self._base_filters = list(base_filters)
        else:
            class_filters = type(self).base_filters
            self._base_filters = list(class_filters) if class_filters else []

    def resolve_criterion(self) -> tuple[str, str] | None:
        for param in type(self).priority:
            value = self._values.get(param)
            if value:
                return param, value
        return None

    def build_domain(self) -> list[list[Any]]:
        resolved = self.resolve_criterion()
        if resolved is None:
            return list(self._base_filters)
        param, value = resolved
        operator = getattr(type(self), param)
        odoo_field = type(self).odoo_fields.get(param, param)
        domain: list[list[Any]] = [[odoo_field, operator.value, value]]
        domain.extend(self._base_filters)
        return domain
