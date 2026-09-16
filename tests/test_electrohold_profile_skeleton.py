from config_store import load_config
from supplier_profile_pipeline import (
    resolve_supplier_profile_fields,
)


def test_electrohold_profile_is_configured():
    config = load_config()

    profile = config["invoice"]["profiles"][
        "electricity_electrohold"
    ]

    assert [
        field["name"]
        for field in profile["fields"]
    ] == [
        "supplier_name",
        "supplier_id",
        "issue_date",
        "due_date",
        "total_amount",
    ]


def test_electrohold_resolves_common_fields_only():
    config = load_config()

    result = resolve_supplier_profile_fields(
        document_config=config["invoice"],
        ocr_text=(
            "Доставчик: "
            "Електрохолд Продажби ЕАД"
        ),
    )

    assert result["profile"] == (
        "electricity_electrohold"
    )
    assert result["requires_review"] is False
    assert result["warnings"] == []

    field_names = [
        field["name"]
        for field in result["fields"]
    ]

    assert len(field_names) == 8
    assert set(field_names) == {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
    }
    assert "contract_number" not in field_names

    supplier_field = next(
        field
        for field in result["fields"]
        if field["name"] == "supplier_name"
    )

    assert supplier_field == {
        "name": "supplier_name",
        "type": "constant",
        "value": "Електрохолд Продажби ЕАД",
        "validation": [
            {
                "type": "required",
                "message": "Supplier name is required",
            }
        ],
    }


def test_a1_profile_still_resolves_nine_fields():
    config = load_config()

    result = resolve_supplier_profile_fields(
        document_config=config["invoice"],
        ocr_text="А1 България ЕАД",
    )

    assert result["profile"] == "telecom_a1"
    assert len(result["fields"]) == 9

    supplier_field = next(
        field
        for field in result["fields"]
        if field["name"] == "supplier_name"
    )

    assert supplier_field["value"] == (
        "А1 България ЕАД"
    )


def test_unknown_supplier_keeps_generic_supplier_field():
    config = load_config()

    result = resolve_supplier_profile_fields(
        document_config=config["invoice"],
        ocr_text="Непознат доставчик ООД",
    )

    assert result["profile"] is None
    assert result["requires_review"] is True

    supplier_field = next(
        field
        for field in result["fields"]
        if field["name"] == "supplier_name"
    )

    assert supplier_field == {
        "name": "supplier_name",
        "type": "llm",
        "validation": [],
    }
