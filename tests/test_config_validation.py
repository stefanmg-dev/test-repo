import copy

import pytest

from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)
from document_config_resolver import (
    resolve_document_fields,
)


PROFILE_NAME = "telecom_a1"


def get_common_fields(
    config: dict,
) -> list:
    return config[
        "invoice"
    ][
        "common_fields"
    ]


def get_profile_fields(
    config: dict,
) -> list:
    return config[
        "invoice"
    ][
        "profiles"
    ][
        PROFILE_NAME
    ][
        "fields"
    ]


def find_common_field(
    config: dict,
    field_name: str,
) -> dict:
    return next(
        field
        for field in get_common_fields(config)
        if field["name"] == field_name
    )


def test_current_document_types_config_is_valid():
    config = load_config()

    validate_config(config)

    assert "invoice" in config

    invoice_config = config["invoice"]

    assert invoice_config[
        "default_profile"
    ] == PROFILE_NAME

    assert len(
        invoice_config["common_fields"]
    ) == 8

    assert len(
        invoice_config["profiles"][
            PROFILE_NAME
        ]["fields"]
    ) == 1

    assert len(
        resolve_document_fields(
            invoice_config
        )
    ) == 9


def test_rejects_duplicate_field_names():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    profile_fields = get_profile_fields(
        invalid_config
    )

    profile_fields.append(
        copy.deepcopy(profile_fields[0])
    )

    with pytest.raises(
        ConfigValidationError,
        match="duplicate field name",
    ):
        validate_config(invalid_config)

def test_rejects_invalid_regex():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    invoice_number_field = find_common_field(
        invalid_config,
        "invoice_number",
    )

    assert invoice_number_field[
        "type"
    ] == "regex_list"

    invoice_number_field["rules"][0] = "("

    with pytest.raises(
        ConfigValidationError,
        match="invalid regex",
    ):
        validate_config(invalid_config)


def test_rejects_unknown_field_type():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    get_common_fields(
        invalid_config
    )[0]["type"] = "unknown_type"

    with pytest.raises(
        ConfigValidationError,
        match="is not supported",
    ):
        validate_config(invalid_config)


def test_rejects_invalid_issue_date_regex():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    issue_date_field = find_common_field(
        invalid_config,
        "issue_date",
    )

    assert issue_date_field[
        "type"
    ] == "regex_list"

    issue_date_field["rules"][0] = "("

    with pytest.raises(
        ConfigValidationError,
        match="invalid regex",
    ):
        validate_config(invalid_config)


def test_issue_date_has_before_and_after_rules():
    config = load_config()

    issue_date_field = find_common_field(
        config,
        "issue_date",
    )

    assert issue_date_field[
        "type"
    ] == "regex_list"

    assert len(
        issue_date_field["rules"]
    ) == 2


def test_rejects_unknown_default_profile():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    invalid_config[
        "invoice"
    ][
        "default_profile"
    ] = "unknown_profile"

    with pytest.raises(
        ConfigValidationError,
        match="default_profile",
    ):
        validate_config(invalid_config)


def test_rejects_duplicate_common_field():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    common_fields = get_common_fields(
        invalid_config
    )

    common_fields.append(
        copy.deepcopy(common_fields[0])
    )

    with pytest.raises(
        ConfigValidationError,
        match="duplicate field name",
    ):
        validate_config(invalid_config)