"""Construcción reutilizable de domains Odoo."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, ClassVar


class OdooOperator(str, Enum):
    EQ = "="
    ILIKE = "ilike"
    GT = ">"


@dataclass
class _OpNode:
    op: str
    left: _DomainNode
    right: _DomainNode


@dataclass
class _LeafNode:
    field: str
    operator: OdooOperator


_DomainNode = _OpNode | _LeafNode


def _parse_template(tokens: list[Any], index: int = 0) -> tuple[_DomainNode, int]:
    if index >= len(tokens):
        raise ValueError("Unexpected end of domain template")
    token = tokens[index]
    if token in ("|", "&"):
        left, index = _parse_template(tokens, index + 1)
        right, index = _parse_template(tokens, index)
        return _OpNode(token, left, right), index
    if isinstance(token, list):
        if len(token) != 2:
            raise ValueError(f"Invalid leaf template: {token}")
        field = token[0]
        operator = token[1]
        if not isinstance(field, str) or not isinstance(operator, OdooOperator):
            raise ValueError(f"Invalid leaf template: {token}")
        return _LeafNode(field, operator), index + 1
    raise ValueError(f"Invalid template token: {token!r}")


def _extract_conditions(domain: list[Any]) -> list[list[Any]]:
    return [item for item in domain if isinstance(item, list)]


def _combine_domains(op: str, left: list[Any] | None, right: list[Any] | None) -> list[Any] | None:
    if left is None and right is None:
        return None
    if left is None:
        return right
    if right is None:
        return left
    conditions = _extract_conditions(left) + _extract_conditions(right)
    if len(conditions) == 1:
        return conditions
    return [op] * (len(conditions) - 1) + conditions


class OdooDomainBuilder:
    """Base para builders de domain con plantilla ``query`` en notación polaca."""

    base_filters: ClassVar[list[Any]] = []
    query: ClassVar[list[Any]] = []

    def __init__(
        self,
        *,
        base_filters: list[Any] | None = None,
        **kwargs: str | None,
    ) -> None:
        self._values = kwargs
        if base_filters is not None:
            self._base_filters = list(base_filters)
        else:
            class_filters = type(self).base_filters
            self._base_filters = list(class_filters) if class_filters else []

    def _resolve_leaf(self, leaf: _LeafNode) -> list[Any] | None:
        value = self._values.get(leaf.field)
        if not value:
            return None
        return [[leaf.field, leaf.operator.value, value]]

    def _resolve_node(self, node: _DomainNode) -> list[Any] | None:
        if isinstance(node, _LeafNode):
            return self._resolve_leaf(node)
        left = self._resolve_node(node.left)
        right = self._resolve_node(node.right)
        return _combine_domains(node.op, left, right)

    def _resolve_query(self) -> list[Any] | None:
        template = type(self).query
        if not template:
            return None
        node, index = _parse_template(list(template))
        if index != len(template):
            raise ValueError("Domain template contains unconsumed tokens")
        return self._resolve_node(node)

    def build_domain(self) -> list[Any]:
        resolved = self._resolve_query()
        if not resolved:
            return list(self._base_filters)
        return [*resolved, *self._base_filters]
