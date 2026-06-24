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
        ["name", "=", "Acme"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_single_vat() -> None:
    assert CustomerSearchDomain(vat="ES123").build_domain() == [
        ["vat", "ilike", "ES123"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_single_email() -> None:
    assert CustomerSearchDomain(email="a@b.com").build_domain() == [
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_two_criteria_or() -> None:
    assert CustomerSearchDomain(name="Acme", email="a@b.com").build_domain() == [
        "|",
        ["name", "=", "Acme"],
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_all_criteria_or() -> None:
    assert CustomerSearchDomain(
        name="Acme",
        vat="ES",
        email="a@b.com",
    ).build_domain() == [
        "|",
        "|",
        ["name", "=", "Acme"],
        ["vat", "ilike", "ES"],
        ["email", "ilike", "a@b.com"],
        *CUSTOMER_BASE_FILTERS,
    ]


def test_build_domain_skips_empty_leaves() -> None:
    assert CustomerSearchDomain(name="Acme", vat=None, email=None).build_domain() == [
        ["name", "=", "Acme"],
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
