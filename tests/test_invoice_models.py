import pytest
from pydantic import ValidationError

from invoice_models import (
    INVOICE_SCHEMA_VERSION,
    UniversalInvoiceModel,
)


def test_universal_invoice_defaults_to_versioned_empty_collections():
    invoice = UniversalInvoiceModel()

    assert invoice.schema_version == INVOICE_SCHEMA_VERSION
    assert invoice.services == []
    assert invoice.metering_points == []
    assert invoice.meters == []
    assert invoice.consumption_items == []


def test_universal_invoice_accepts_current_provider_fields():
    invoice = UniversalInvoiceModel.model_validate(
        {
            "supplier_name": "Supplier",
            "invoice_number": "INV-1",
            "total_amount": "67.96",
            "contract_number": "A1-CONTRACT",
            "client_number": "CLIENT-1",
            "abonat_number": "ABONAT-1",
            "total_consumption": "123.45",
            "business_partner_number": "BP-1",
            "contract_account_number": "CA-1",
            "installation_number": "INSTALL-1",
            "services": [
                {
                    "description": "Heating",
                    "unit": "MWh",
                    "quantity": "1.25",
                    "unit_price": "10.00",
                    "amount": "12.50",
                }
            ],
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
        }
    )

    assert invoice.contract_number == "A1-CONTRACT"
    assert invoice.services[0].amount == "12.50"
    assert invoice.meters[0].meter_number == "METER-1"
    assert invoice.consumption_items[0].difference == "50"


def test_universal_invoice_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        UniversalInvoiceModel.model_validate(
            {"unknown_invoice_field": "value"}
        )


def test_universal_invoice_rejects_unknown_collection_fields():
    with pytest.raises(ValidationError):
        UniversalInvoiceModel.model_validate(
            {
                "services": [
                    {
                        "description": "Heating",
                        "unknown_service_field": "value",
                    }
                ]
            }
        )


def test_universal_invoice_json_schema_is_stable():
    schema = UniversalInvoiceModel.model_json_schema()

    assert schema["properties"]["schema_version"]["default"] == "1"
    assert schema["properties"]["services"]["type"] == "array"
    assert schema["properties"]["metering_points"]["type"] == "array"
    assert schema["properties"]["meters"]["type"] == "array"
    assert schema["properties"]["consumption_items"]["type"] == "array"
    assert schema["additionalProperties"] is False
