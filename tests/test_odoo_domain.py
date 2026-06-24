"""Unit tests for OdooDomainBuilder."""

from __future__ import annotations

from app.utils.odoo_domain import OdooDomainBuilder, OdooOperator


class AndDomain(OdooDomainBuilder):
    query = [
        "&",
        ["name", OdooOperator.EQ],
        ["email", OdooOperator.ILIKE],
    ]


def test_build_domain_and_template() -> None:
    assert AndDomain(name="Acme", email="a@b.com").build_domain() == [
        "&",
        ["name", "=", "Acme"],
        ["email", "ilike", "a@b.com"],
    ]


def test_build_domain_and_template_partial() -> None:
    assert AndDomain(name="Acme").build_domain() == [["name", "=", "Acme"]]
