from config_store import load_config
from result_validator import validate_result


VALID_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "supplier_id": "131468980",
    "invoice_number": "0726592493",
    "issue_date": "19.08.2026",
    "contract_number": "М5781970",
    "customer_name": "Стефан Момчилов Георгиев",
    "customer_address": (
        "жк.Красно село бл.201А вх.Г ет.2 ап.68"
    ),
    "due_date": "13.09.2026",
    "total_amount": "67.96",
}


def test_valid_a1_result_passes_validation():
    config = load_config()

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=VALID_VALUES
    )

    assert validation == {
        "valid": True,
        "errors": {}
    }


def test_missing_required_value_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "invoice_number": None,
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["invoice_number"] == [
        "Invoice number is required"
    ]


def test_invalid_invoice_number_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "invoice_number": "ABC123",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["invoice_number"] == [
        "Invoice number must contain between 8 and 15 digits"
    ]


def test_invalid_supplier_id_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "supplier_id": "ABC",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["supplier_id"] == [
        "Supplier ID must contain between 9 and 13 digits"
    ]


def test_invalid_calendar_date_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "issue_date": "31.02.2026",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["issue_date"] == [
        "Issue date must be a valid date in DD.MM.YYYY format"
    ]


def test_invalid_due_date_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "due_date": "99.99.2026",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["due_date"] == [
        "Due date must be a valid date in DD.MM.YYYY format"
    ]


def test_invalid_contract_number_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "contract_number": "INVALID",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["contract_number"] == [
        "Contract number has invalid format"
    ]


def test_non_positive_total_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "total_amount": "0.00",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["total_amount"] == [
        "Total amount must be a positive decimal number"
    ]


def test_invalid_decimal_total_is_rejected():
    config = load_config()

    invalid_values = {
        **VALID_VALUES,
        "total_amount": "invalid",
    }

    validation = validate_result(
        document_type="invoice",
        config=config,
        final_values=invalid_values
    )

    assert validation["valid"] is False

    assert validation["errors"]["total_amount"] == [
        "Total amount must be a positive decimal number"
    ]


def test_unknown_document_type_is_rejected():
    config = load_config()

    validation = validate_result(
        document_type="unknown",
        config=config,
        final_values={}
    )

    assert validation == {
        "valid": False,
        "errors": {
            "_document_type": [
                "Unknown document type: unknown"
            ]
        }
    }