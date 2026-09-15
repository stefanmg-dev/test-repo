from document_config_resolver import (
    resolve_document_fields,
)


DOCUMENT_CONFIG = {
    "default_profile": "telecom_a1",
    "common_fields": [
        {
            "name": "invoice_number",
            "type": "regex",
            "rule": "([0-9]+)",
        },
        {
            "name": "total_amount",
            "type": "regex",
            "rule": "([0-9]+[.,][0-9]+)",
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


def test_default_resolution_still_uses_a1_profile():
    fields = resolve_document_fields(
        DOCUMENT_CONFIG
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "total_amount",
        "contract_number",
    ]


def test_common_only_resolution_ignores_default_profile():
    fields = resolve_document_fields(
        DOCUMENT_CONFIG,
        use_default_profile=False,
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "total_amount",
    ]


def test_explicit_profile_overrides_common_only_mode():
    fields = resolve_document_fields(
        DOCUMENT_CONFIG,
        profile_name="telecom_a1",
        use_default_profile=False,
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "total_amount",
        "contract_number",
    ]


def test_common_only_resolution_returns_deep_copy():
    fields = resolve_document_fields(
        DOCUMENT_CONFIG,
        use_default_profile=False,
    )

    fields[0]["name"] = "modified"

    assert DOCUMENT_CONFIG[
        "common_fields"
    ][0]["name"] == "invoice_number"
