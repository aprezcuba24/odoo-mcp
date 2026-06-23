"""Unit tests for ObjectResponse and ListResponse."""

from __future__ import annotations

from app.services.customers import PartnerResponse
from app.utils.object_response import ListResponse, Normalizer, ObjectResponse


class SampleResponse(ObjectResponse):
    id = Normalizer.RAW
    label = Normalizer.DEFAULT_EMPTY
    email = Normalizer.OPTIONAL


class MappedResponse(ObjectResponse):
    odoo_fields = {"label": "display_name"}

    label = Normalizer.DEFAULT_EMPTY


def test_object_response_raw() -> None:
    result = SampleResponse().render({"id": 42, "label": "Acme", "email": "a@b.com"})
    assert result["id"] == 42


def test_object_response_optional_false_to_none() -> None:
    result = SampleResponse().render({"id": 1, "label": "Acme", "email": False})
    assert result["email"] is None


def test_object_response_optional_none_to_none() -> None:
    result = SampleResponse().render({"id": 1, "label": "Acme", "email": None})
    assert result["email"] is None


def test_object_response_optional_coerces_to_str() -> None:
    result = SampleResponse().render({"id": 1, "label": "Acme", "email": 123})
    assert result["email"] == "123"


def test_object_response_default_empty_falsy_to_empty_str() -> None:
    result = SampleResponse().render({"id": 1, "label": False, "email": None})
    assert result["label"] == ""


def test_object_response_default_empty_preserves_value() -> None:
    result = SampleResponse().render({"id": 1, "label": "Acme", "email": None})
    assert result["label"] == "Acme"


def test_object_response_odoo_fields_mapping() -> None:
    result = MappedResponse().render({"display_name": "Mapped"})
    assert result == {"label": "Mapped"}


def test_object_response_render_many() -> None:
    records = [
        {"id": 1, "label": "A", "email": None},
        {"id": 2, "label": "B", "email": "b@c.com"},
    ]
    assert SampleResponse().render_many(records) == [
        {"id": 1, "label": "A", "email": None},
        {"id": 2, "label": "B", "email": "b@c.com"},
    ]


def test_partner_response_false_to_none() -> None:
    normalized = PartnerResponse().render(
        {
            "id": 1,
            "name": "Acme",
            "email": False,
            "phone": False,
            "vat": "ES123",
        }
    )
    assert normalized == {
        "id": 1,
        "name": "Acme",
        "email": None,
        "phone": None,
        "vat": "ES123",
    }


def test_list_response_empty() -> None:
    result = ListResponse(PartnerResponse(), items_key="customers").empty(
        message="No criteria",
    )
    assert result == {
        "count": 0,
        "customers": [],
        "search": None,
        "message": "No criteria",
    }


def test_list_response_build() -> None:
    records = [
        {"id": 1, "name": "Acme", "email": False, "phone": False, "vat": "ES1"},
    ]
    result = ListResponse(PartnerResponse(), items_key="customers").build(
        records,
        search={"mode": "query", "value": "Acme"},
        message=None,
    )
    assert result == {
        "count": 1,
        "customers": [
            {"id": 1, "name": "Acme", "email": None, "phone": None, "vat": "ES1"},
        ],
        "search": {"mode": "query", "value": "Acme"},
        "message": None,
    }
