from copy import deepcopy

import pytest
from pydantic import ValidationError

from invoice_mapper import map_extraction_to_universal_invoice
from invoice_models import INVOICE_SCHEMA_VERSION


def test_maps_a1_invoice_fields():
    invoice = map_extraction_to_universal_invoice(
        document_type="invoice",
        final_values={
            "supplier_name": "A1",
            "invoice_number": "INV-1",
            "contract_number": "CONTRACT-1",
        },
        collections={},
    )

    assert invoice is not None
    assert invoice.schema_version == INVOICE_SCHEMA_VERSION
    assert invoice.supplier_name == "A1"
    assert invoice.contract_number == "CONTRACT-1"
    assert invoice.services == []


def test_maps_electrohold_invoice_fields_and_collections():
    invoice = map_extraction_to_universal_invoice(
        document_type="invoice",
        final_values={
            "supplier_name": "Electrohold",
            "client_number": "CLIENT-1",
            "abonat_number": "ABONAT-1",
            "total_consumption": "50",
        },
        collections={
            "metering_points": [
                {"metering_point_number": "MP-1"}
            ],
            "meters": [{"meter_number": "METER-1"}],
            "consumption_items": [
                {
                    "tariff": "day",
                    "previous_reading": "100",
                    "current_reading": "150",
                    "difference": "50",
                    "correction": "0",
                    "quantity": "50",
                    "unit": "kWh",
                }
            ],
        },
    )

    assert invoice is not None
    assert invoice.client_number == "CLIENT-1"
    assert invoice.meters[0].meter_number == "METER-1"
    assert invoice.consumption_items[0].difference == "50"


def test_maps_toplofikacia_invoice_fields_and_services():
    invoice = map_extraction_to_universal_invoice(
        document_type="invoice",
        final_values={
            "supplier_name": "Toplofikacia Sofia",
            "business_partner_number": "BP-1",
            "contract_account_number": "CA-1",
            "installation_number": "INSTALL-1",
        },
        collections={
            "services": [
                {
                    "description": "Heating",
                    "unit": "MWh",
                    "quantity": "1.25",
                    "unit_price": "10.00",
                    "amount": "12.50",
                }
            ]
        },
    )

    assert invoice is not None
    assert invoice.business_partner_number == "BP-1"
    assert invoice.services[0].amount == "12.50"


def test_generic_invoice_ignores_unknown_extraction_fields():
    invoice = map_extraction_to_universal_invoice(
        document_type="invoice",
        final_values={
            "supplier_name": "Unknown supplier",
            "unknown_profile_field": "unmapped",
        },
        collections={
            "unknown_collection": [{"value": "unmapped"}]
        },
    )

    assert invoice is not None
    assert invoice.supplier_name == "Unknown supplier"
    assert "unknown_profile_field" not in invoice.model_dump()
    assert invoice.services == []


def test_non_invoice_document_is_not_mapped():
    assert map_extraction_to_universal_invoice(
        document_type="receipt",
        final_values={},
        collections={},
    ) is None


def test_mapping_does_not_mutate_source_dictionaries():
    final_values = {"supplier_name": "Supplier"}
    collections = {
        "services": [
            {
                "description": "Heating",
                "amount": "12.50",
            }
        ]
    }
    original_values = deepcopy(final_values)
    original_collections = deepcopy(collections)

    invoice = map_extraction_to_universal_invoice(
        document_type="invoice",
        final_values=final_values,
        collections=collections,
    )
    assert invoice is not None
    invoice.services[0].description = "Changed"

    assert final_values == original_values
    assert collections == original_collections


def test_mapping_validates_known_collection_items():
    with pytest.raises(ValidationError):
        map_extraction_to_universal_invoice(
            document_type="invoice",
            final_values={},
            collections={
                "meters": [
                    {
                        "meter_number": "METER-1",
                        "unexpected": "value",
                    }
                ]
            },
        )
