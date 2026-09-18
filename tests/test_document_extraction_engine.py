from extraction_orchestrator import (
    apply_rules,
    extract_document_data,
)


def build_config() -> dict:
    return {
        "invoice": {
            "common_fields": [
                {
                    "name": "invoice_number",
                    "type": "regex",
                    "rule": r"Фактура № ([0-9]+)",
                    "occurrence": "first",
                    "validation": [],
                }
            ],
            "profiles": {
                "electricity_electrohold": {
                    "fields": [],
                    "collections": {
                        "meters": {
                            "start_pattern": r"^Електромер\s*№",
                            "fields": [
                                {
                                    "name": "meter_number",
                                    "type": "regex",
                                    "rule": (
                                        r"Електромер\s*№\s*"
                                        r"([0-9]{8,15})"
                                    ),
                                    "occurrence": "first",
                                    "validation": [],
                                }
                            ],
                        }
                    },
                }
            },
            "collections": {
                "services": {
                    "cardinality": "zero_or_more",
                    "fields": [],
                },
                "meters": {
                    "cardinality": "zero_or_more",
                    "fields": [],
                },
            },
        }
    }


def test_extracts_fields_and_resolved_collections():
    result = extract_document_data(
        document_type="invoice",
        config=build_config(),
        raw_text=(
            "Фактура № 0484935637\n"
            "Електромер № 1021015029"
        ),
        llm_values={},
        profile_name="electricity_electrohold",
    )

    assert result == {
        "fields": {
            "invoice_number": "0484935637",
        },
        "collections": {
            "services": [],
            "meters": [
                {"meter_number": "1021015029"}
            ],
        },
        "collection_validation": {
            "valid": True,
            "errors": {},
        },
    }


def test_apply_rules_remains_backward_compatible():
    assert apply_rules(
        document_type="invoice",
        config=build_config(),
        raw_text="Фактура № 0484935637",
        llm_values={},
        resolved_fields=[
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": r"Фактура № ([0-9]+)",
                "occurrence": "first",
                "validation": [],
            }
        ],
    ) == {
        "invoice_number": "0484935637"
    }


def test_returns_existing_unknown_document_error_shape():
    assert extract_document_data(
        document_type="unknown",
        config=build_config(),
        raw_text="sample",
        llm_values={},
    ) == {
        "error": "Unknown document type: unknown"
    }


def test_reports_collection_validation_separately():
    config = build_config()
    config["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["fields"][0][
        "validation"
    ] = [
        {
            "type": "regex",
            "pattern": r"[0-9]{10}",
            "message": "Meter number is invalid",
        }
    ]

    result = extract_document_data(
        document_type="invoice",
        config=config,
        raw_text=(
            "Фактура № 0484935637\n"
            "Електромер № 12345678"
        ),
        llm_values={},
        profile_name="electricity_electrohold",
    )

    assert result["fields"] == {
        "invoice_number": "0484935637"
    }
    assert result["collection_validation"] == {
        "valid": False,
        "errors": {
            "meters[0].meter_number": [
                "Meter number is invalid"
            ]
        },
    }
