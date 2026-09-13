from document_status import (
    build_document_type_metadata,
    is_document_type_ready,
)
from extraction_orchestrator import apply_rules
from result_validator import validate_result


PROFILE_CONFIG = {
    "invoice": {
        "default_profile": "telecom_a1",
        "common_fields": [
            {
                "name": "supplier_name",
                "type": "constant",
                "value": "А1 България ЕАД",
                "validation": [
                    {
                        "type": "required",
                        "message": (
                            "Supplier name is required"
                        ),
                    }
                ],
            },
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": (
                    "Фактура\\s*"
                    "([0-9]{10})"
                ),
                "occurrence": "first",
                "validation": [
                    {
                        "type": "required",
                        "message": (
                            "Invoice number is required"
                        ),
                    }
                ],
            },
        ],
        "profiles": {
            "telecom_a1": {
                "fields": [
                    {
                        "name": "contract_number",
                        "type": "regex",
                        "rule": (
                            "Договор\\s*"
                            "([МM][0-9]{7})"
                        ),
                        "occurrence": "first",
                        "validation": [
                            {
                                "type": "required",
                                "message": (
                                    "Contract number "
                                    "is required"
                                ),
                            }
                        ],
                    }
                ]
            }
        },
    }
}


RAW_TEXT = """
Фактура 0726592493
Договор М5781970
""".strip()


EXPECTED_VALUES = {
    "supplier_name": "А1 България ЕАД",
    "invoice_number": "0726592493",
    "contract_number": "М5781970",
}


def test_profile_document_is_ready():
    document_config = PROFILE_CONFIG[
        "invoice"
    ]

    assert is_document_type_ready(
        document_config
    ) is True


def test_profile_metadata_counts_resolved_fields():
    document_config = PROFILE_CONFIG[
        "invoice"
    ]

    assert build_document_type_metadata(
        document_config
    ) == {
        "status": "ready",
        "ready": True,
        "field_count": 3,
    }


def test_profile_fields_are_extracted():
    final_values = apply_rules(
        document_type="invoice",
        config=PROFILE_CONFIG,
        raw_text=RAW_TEXT,
        llm_values={},
    )

    assert final_values == EXPECTED_VALUES


def test_profile_fields_are_validated():
    validation = validate_result(
        document_type="invoice",
        config=PROFILE_CONFIG,
        final_values=EXPECTED_VALUES,
    )

    assert validation == {
        "valid": True,
        "errors": {},
    }


def test_missing_profile_field_is_reported():
    final_values = {
        "supplier_name": "А1 България ЕАД",
        "invoice_number": "0726592493",
        "contract_number": None,
    }

    validation = validate_result(
        document_type="invoice",
        config=PROFILE_CONFIG,
        final_values=final_values,
    )

    assert validation == {
        "valid": False,
        "errors": {
            "contract_number": [
                "Contract number is required"
            ]
        },
    }