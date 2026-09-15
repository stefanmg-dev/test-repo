from document_config_resolver import (
    resolve_document_fields,
)
from profile_selection import (
    select_document_profile,
)


DOCUMENT_CONFIG = {
    "default_profile": "telecom_a1",
    "common_fields": [
        {
            "name": "supplier_name",
            "type": "constant",
            "value": "Test Supplier",
        },
        {
            "name": "invoice_number",
            "type": "regex",
            "rule": "([0-9]+)",
        },
    ],
    "profiles": {
        "telecom_a1": {
            "fields": [
                {
                    "name": "contract_number",
                    "type": "regex",
                    "rule": "([МM][0-9]+)",
                }
            ]
        }
    },
}


def resolve_selected_fields(
    matched_profile_name,
):
    selection = select_document_profile(
        document_config=DOCUMENT_CONFIG,
        matched_profile_name=matched_profile_name,
    )

    fields = resolve_document_fields(
        document_config=DOCUMENT_CONFIG,
        profile_name=selection["profile"],
        use_default_profile=selection[
            "use_default_profile"
        ],
    )

    return selection, fields


def test_known_selection_resolves_profile_fields():
    selection, fields = resolve_selected_fields(
        "telecom_a1"
    )

    assert selection[
        "profile"
    ] == "telecom_a1"

    assert selection[
        "requires_review"
    ] is False

    assert selection["warnings"] == []

    assert [
        field["name"]
        for field in fields
    ] == [
        "supplier_name",
        "invoice_number",
        "contract_number",
    ]


def test_unknown_selection_resolves_common_fields_only():
    selection, fields = resolve_selected_fields(
        None
    )

    assert selection["profile"] is None

    assert selection[
        "use_default_profile"
    ] is False

    assert selection[
        "requires_review"
    ] is True

    assert [
        warning["code"]
        for warning in selection["warnings"]
    ] == [
        "unknown_supplier_profile"
    ]

    assert [
        field["name"]
        for field in fields
    ] == [
        "supplier_name",
        "invoice_number",
    ]


def test_unknown_selection_excludes_profile_field():
    _, fields = resolve_selected_fields(
        None
    )

    field_names = {
        field["name"]
        for field in fields
    }

    assert "contract_number" not in field_names


def test_known_and_unknown_resolutions_are_independent():
    _, known_fields = resolve_selected_fields(
        "telecom_a1"
    )

    _, unknown_fields = resolve_selected_fields(
        None
    )

    known_fields[0]["name"] = "modified"

    assert unknown_fields[0]["name"] == (
        "supplier_name"
    )

    assert DOCUMENT_CONFIG[
        "common_fields"
    ][0]["name"] == "supplier_name"
