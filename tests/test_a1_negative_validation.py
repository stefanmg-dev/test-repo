from copy import deepcopy

import pytest

from config_store import load_config
from result_validator import validate_result


VALID_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": (
        "жк Красно село "
        "бл.201А вх.Г ет 2 ап. 68"
    ),
    "due_date": "13.09.2026",
    "total_amount": "67.96",
    "contract_number": "M5781970",
}


@pytest.mark.parametrize(
    (
        "field_name",
        "invalid_value",
        "expected_message",
    ),
    [
        (
            "invoice_number",
            None,
            "Invoice number is required",
        ),
        (
            "contract_number",
            None,
            "Contract number is required",
        ),
        (
            "total_amount",
            None,
            "Total amount is required",
        ),
        (
            "supplier_id",
            "ABC",
            (
                "Supplier ID must contain "
                "between 9 and 13 digits"
            ),
        ),
        (
            "issue_date",
            "31.02.2026",
            (
                "Issue date must be a valid "
                "date in DD.MM.YYYY format"
            ),
        ),
        (
            "due_date",
            "99.99.2026",
            (
                "Due date must be a valid "
                "date in DD.MM.YYYY format"
            ),
        ),
        (
            "total_amount",
            "invalid",
            (
                "Total amount must be a "
                "positive decimal number"
            ),
        ),
        (
            "total_amount",
            "0.00",
            (
                "Total amount must be a "
                "positive decimal number"
            ),
        ),
    ],
)
def test_a1_invalid_field_is_reported(
    field_name,
    invalid_value,
    expected_message,
):
    config = load_config()
    final_values = deepcopy(VALID_VALUES)

    final_values[field_name] = invalid_value

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=final_values,
    )

    assert validation["valid"] is False

    assert field_name in validation["errors"]

    assert expected_message in validation[
        "errors"
    ][field_name]


def test_a1_valid_values_pass_validation():
    config = load_config()

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=deepcopy(VALID_VALUES),
    )

    assert validation == {
        "valid": True,
        "errors": {},
    }


def test_multiple_missing_fields_are_reported():
    config = load_config()
    final_values = deepcopy(VALID_VALUES)

    final_values["invoice_number"] = None
    final_values["contract_number"] = None
    final_values["total_amount"] = None

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=final_values,
    )

    assert validation["valid"] is False

    assert set(validation["errors"]) == {
        "invoice_number",
        "contract_number",
        "total_amount",
    }
