import pytest

from document_config_resolver import (
    DocumentConfigResolutionError,
    resolve_document_fields,
)


def build_profile_config(
    default_profile=None,
):
    config = {
        "common_fields": [
            {
                "name": "invoice_number",
                "type": "regex",
                "rule": "([0-9]+)",
            }
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

    if default_profile is not None:
        config["default_profile"] = (
            default_profile
        )

    return config


def test_uses_explicit_profile_name():
    document_config = build_profile_config(
        default_profile="telecom_a1"
    )

    fields = resolve_document_fields(
        document_config=document_config,
        profile_name="telecom_a1",
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "contract_number",
    ]


def test_uses_configured_default_profile():
    document_config = build_profile_config(
        default_profile="telecom_a1"
    )

    fields = resolve_document_fields(
        document_config=document_config
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "contract_number",
    ]


def test_explicit_profile_overrides_default():
    document_config = build_profile_config(
        default_profile="telecom_a1"
    )

    document_config["profiles"][
        "electricity_evn"
    ] = {
        "fields": [
            {
                "name": "customer_number",
                "type": "regex",
                "rule": "([0-9]+)",
            }
        ]
    }

    fields = resolve_document_fields(
        document_config=document_config,
        profile_name="electricity_evn",
    )

    assert [
        field["name"]
        for field in fields
    ] == [
        "invoice_number",
        "customer_number",
    ]


def test_missing_default_profile_is_rejected():
    document_config = build_profile_config()

    with pytest.raises(
        DocumentConfigResolutionError,
        match="profile name is required",
    ):
        resolve_document_fields(
            document_config=document_config
        )


def test_unknown_default_profile_is_rejected():
    document_config = build_profile_config(
        default_profile="unknown_profile"
    )

    with pytest.raises(
        DocumentConfigResolutionError,
        match="was not found",
    ):
        resolve_document_fields(
            document_config=document_config
        )


def test_default_profile_must_be_string():
    document_config = build_profile_config()

    document_config["default_profile"] = 123

    with pytest.raises(
        DocumentConfigResolutionError,
        match="default_profile",
    ):
        resolve_document_fields(
            document_config=document_config
        )