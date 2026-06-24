"""Renderizado reutilizable de registros Odoo y envelopes de lista."""

from __future__ import annotations

from enum import Enum
from typing import Any, ClassVar


class Normalizer(str, Enum):
    RAW = "raw"
    OPTIONAL = "optional"
    DEFAULT_EMPTY = "default_empty"


def _apply_normalizer(normalizer: Normalizer, value: Any) -> Any:
    if normalizer is Normalizer.RAW:
        return value
    if normalizer is Normalizer.OPTIONAL:
        if value is False or value is None:
            return None
        return str(value)
    if normalizer is Normalizer.DEFAULT_EMPTY:
        return str(value) if value else ""
    raise ValueError(f"Unknown normalizer: {normalizer}")


class ObjectResponse:
    """Base para renderizar registros con normalizadores declarados por atributo de clase."""

    odoo_fields: ClassVar[dict[str, str]] = {}

    def _field_normalizers(self) -> dict[str, Normalizer]:
        return {
            name: value
            for name, value in vars(type(self)).items()
            if isinstance(value, Normalizer)
        }

    def render(self, record: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field, normalizer in self._field_normalizers().items():
            source = type(self).odoo_fields.get(field, field)
            result[field] = _apply_normalizer(normalizer, record.get(source))
        return result

    def render_many(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self.render(record) for record in records]


class ListResponse:
    """Envelope de respuesta para listas normalizadas con un ``ObjectResponse``."""

    def __init__(self, renderer: ObjectResponse, *, items_key: str) -> None:
        self._renderer = renderer
        self._items_key = items_key

    def empty(self, *, message: str) -> dict[str, Any]:
        return {
            "count": 0,
            self._items_key: [],
            "message": message,
        }

    def build(
        self,
        records: list[dict[str, Any]],
        *,
        message: str | None = None,
    ) -> dict[str, Any]:
        items = self._renderer.render_many(records)
        return {
            "count": len(items),
            self._items_key: items,
            "message": message,
        }
