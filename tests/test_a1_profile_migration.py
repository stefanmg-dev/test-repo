from config_store import load_config
from config_validator import validate_config
from document_config_resolver import (
    resolve_document_fields,
)


PROFILE_NAME = "telecom_a1"
PROFILE_FIELD_NAME = "contract_number"

EXPECTED_FIELD_NAMES = {
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


def get_invoice_config() -> dict:
    config = load_config()

    return config["invoice"]


def test_a1_profile_contains_eight_common_fields():
    invoice_config = get_invoice_config()

    common_fields = invoice_config[
        "common_fields"
    ]

    assert len(common_fields) == 8

    assert PROFILE_FIELD_NAME not in {
        field["name"]
        for field in common_fields
    }


def test_a1_profile_contains_contract_number():
    invoice_config = get_invoice_config()

    profile_fields = invoice_config[
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


def test_a1_default_profile_is_configured():
    invoice_config = get_invoice_config()

    assert invoice_config[
        "default_profile"
    ] == PROFILE_NAME


def test_a1_profile_configuration_is_valid():
    config = load_config()

    validate_config(config)


def test_resolved_a1_profile_has_nine_fields():
    invoice_config = get_invoice_config()

    resolved_fields = resolve_document_fields(
        document_config=invoice_config
    )

    assert len(resolved_fields) == 9


def test_explicit_a1_profile_has_nine_fields():
    invoice_config = get_invoice_config()

    resolved_fields = resolve_document_fields(
        document_config=invoice_config,
        profile_name=PROFILE_NAME,
    )

    assert len(resolved_fields) == 9


def test_resolved_a1_field_names_are_complete():
    invoice_config = get_invoice_config()

    resolved_fields = resolve_document_fields(
        document_config=invoice_config
    )

    assert {
        field["name"]
        for field in resolved_fields
    } == EXPECTED_FIELD_NAMES


def test_default_and_explicit_profile_resolve_equally():
    invoice_config = get_invoice_config()

    default_fields = resolve_document_fields(
        document_config=invoice_config
    )

    explicit_fields = resolve_document_fields(
        document_config=invoice_config,
        profile_name=PROFILE_NAME,
    )

    assert default_fields == explicit_fields
