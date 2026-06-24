"""Unit tests for OdooDomainBuilder."""

from __future__ import annotations

from app.services.customers import CustomerSearchDomain
from app.utils.odoo_domain import OdooDomainBuilder, OdooOperator

CUSTOMER_BASE_FILTERS = CustomerSearchDomain.base_filters


class AndDomain(OdooDomainBuilder):
    query = [
        "&",
        ["name", OdooOperator.EQ],
        ["email", OdooOperator.ILIKE],
    ]


def test_build_domain_without_criteria() -> None:
    assert CustomerSearchDomain().build_domain() == CUSTOMER_BASE_FILTERS


def test_build_domain_single_name() -> None:
    assert CustomerSearchDomain(name="Acme").build_domain() == [
        ["name", "ilike", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_single_phone() -> None:
    assert CustomerSearchDomain(phone="555").build_domain() == [
        ["phone", "ilike", "555"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_query_or_double() -> None:
    assert CustomerSearchDomain(name="Deco", phone="Deco").build_domain() == [
        "|",
        ["name", "ilike", "Deco"],
        ["phone", "ilike", "Deco"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_skips_empty_leaves() -> None:
    assert CustomerSearchDomain(name="Acme", phone=None).build_domain() == [
        ["name", "ilike", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_and_template() -> None:
    assert AndDomain(name="Acme", email="a@b.com").build_domain() == [
        "&",
        ["name", "=", "Acme"],
        ["email", "ilike", "a@b.com"],
    ]


def test_build_domain_and_template_partial() -> None:
    assert AndDomain(name="Acme").build_domain() == [["name", "=", "Acme"]]
