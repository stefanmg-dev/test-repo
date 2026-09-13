from copy import deepcopy

from config_store import load_config
from config_validator import validate_config
from document_config_resolver import (
    resolve_document_fields,
)


PROFILE_NAME = "telecom_a1"
PROFILE_FIELD_NAME = "contract_number"


def build_a1_profile_configuration() -> dict:
    current_config = load_config()

    legacy_fields = deepcopy(
        current_config["invoice"]["fields"]
    )

    common_fields = [
        field
        for field in legacy_fields
        if field["name"] != PROFILE_FIELD_NAME
    ]

    profile_fields = [
        field
        for field in legacy_fields
        if field["name"] == PROFILE_FIELD_NAME
    ]

    return {
        "invoice": {
            "common_fields": common_fields,
            "profiles": {
                PROFILE_NAME: {
                    "fields": profile_fields
                }
            },
        }
    }


def test_a1_profile_contains_eight_common_fields():
    profile_config = (
        build_a1_profile_configuration()
    )

    common_fields = profile_config[
        "invoice"
    ][
        "common_fields"
    ]

    assert len(common_fields) == 8

    assert PROFILE_FIELD_NAME not in {
        field["name"]
        for field in common_fields
    }


def test_a1_profile_contains_contract_number():
    profile_config = (
        build_a1_profile_configuration()
    )

    profile_fields = profile_config[
        "invoice"
    ][
        "profiles"
    ][
        PROFILE_NAME
    ][
        "fields"
    ]

    assert len(profile_fields) == 1

    assert profile_fields[0]["name"] == (
        PROFILE_FIELD_NAME
    )


def test_a1_profile_configuration_is_valid():
    profile_config = (
        build_a1_profile_configuration()
    )

    validate_config(profile_config)


def test_resolved_a1_profile_has_nine_fields():
    profile_config = (
        build_a1_profile_configuration()
    )

    resolved_fields = resolve_document_fields(
        document_config=profile_config[
            "invoice"
        ],
        profile_name=PROFILE_NAME,
    )

    assert len(resolved_fields) == 9


def test_resolved_a1_profile_preserves_all_fields():
    current_config = load_config()

    legacy_fields = current_config[
        "invoice"
    ][
        "fields"
    ]

    profile_config = (
        build_a1_profile_configuration()
    )

    resolved_fields = resolve_document_fields(
        document_config=profile_config[
            "invoice"
        ],
        profile_name=PROFILE_NAME,
    )

    legacy_fields_by_name = {
        field["name"]: field
        for field in legacy_fields
    }

    resolved_fields_by_name = {
        field["name"]: field
        for field in resolved_fields
    }

    assert resolved_fields_by_name == (
        legacy_fields_by_name
    )


def test_resolved_a1_field_names_are_complete():
    profile_config = (
        build_a1_profile_configuration()
    )

    resolved_fields = resolve_document_fields(
        document_config=profile_config[
            "invoice"
        ],
        profile_name=PROFILE_NAME,
    )

    assert {
        field["name"]
        for field in resolved_fields
    } == {
        "supplier_name",
        "supplier_id",
        "invoice_number",
        "issue_date",
        "contract_number",
        "customer_name",
        "customer_address",
        "due_date",
        "total_amount",
    }