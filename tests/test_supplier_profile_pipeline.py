import pytest

from supplier_profile_pipeline import (
    SupplierProfilePipelineError,
    resolve_supplier_profile_fields,
)


COMMON_FIELD = {
    "name": "invoice_number",
    "type": "text",
}

A1_FIELD = {
    "name": "contract_number",
    "type": "text",
}

DOCUMENT_CONFIG = {
    "default_profile": "telecom_a1",
    "common_fields": [
        COMMON_FIELD,
    ],
    "profiles": {
        "telecom_a1": {
            "fields": [
                A1_FIELD,
            ],
        },
        "electricity_evn": {
            "fields": [
                {
                    "name": "meter_number",
                    "type": "text",
                }
            ],
        },
    },
}


def test_a1_supplier_resolves_common_and_profile_fields():
    result = resolve_supplier_profile_fields(
        document_config=DOCUMENT_CONFIG,
        ocr_text=(
            "Доставчик: А1 България ЕАД"
        ),
    )

    assert result["profile"] == (
        "telecom_a1"
    )

    assert result["fields"] == [
        COMMON_FIELD,
        A1_FIELD,
    ]

    assert result[
        "requires_review"
    ] is False

    assert result["warnings"] == []

    assert result[
        "supplier_evidence"
    ]


def test_unknown_supplier_resolves_common_fields_only():
    result = resolve_supplier_profile_fields(
        document_config=DOCUMENT_CONFIG,
        ocr_text=(
            "Непознат доставчик ООД"
        ),
    )

    assert result["profile"] is None

    assert result["fields"] == [
        COMMON_FIELD,
    ]

    assert result[
        "requires_review"
    ] is True

    assert result["warnings"] == [
        {
            "code": (
                "unknown_supplier_profile"
            ),
            "message": (
                "No matching supplier profile "
                "was found"
            ),
        }
    ]

    assert result[
        "supplier_evidence"
    ] == []


def test_unknown_supplier_does_not_use_default_profile():
    result = resolve_supplier_profile_fields(
        document_config=DOCUMENT_CONFIG,
        ocr_text="Софийска вода АД",
    )

    field_names = [
        field["name"]
        for field in result["fields"]
    ]

    assert "invoice_number" in field_names
    assert "contract_number" not in (
        field_names
    )


@pytest.mark.parametrize(
    "invalid_config",
    [
        None,
        [],
        "invoice",
    ],
)
def test_rejects_invalid_document_configuration(
    invalid_config,
):
    with pytest.raises(
        SupplierProfilePipelineError,
        match="must be an object",
    ):
        resolve_supplier_profile_fields(
            document_config=invalid_config,
            ocr_text="А1 България ЕАД",
        )