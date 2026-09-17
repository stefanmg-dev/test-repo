import copy

import pytest

from config_store import load_config
from config_validator import ConfigValidationError, validate_config
from document_config_resolver import resolve_document_fields


PROFILE_NAME = "telecom_a1"


def get_common_fields(config: dict) -> list:
    return config["invoice"]["common_fields"]


def get_profile_fields(config: dict) -> list:
    return config["invoice"]["profiles"][PROFILE_NAME]["fields"]


def find_common_field(config: dict, field_name: str) -> dict:
    return next(
        field
        for field in get_common_fields(config)
        if field["name"] == field_name
    )


def test_current_document_types_config_is_valid():
    config = load_config()
    validate_config(config)
    invoice = config["invoice"]
    assert invoice["default_profile"] == PROFILE_NAME
    assert len(invoice["common_fields"]) == 8
    assert len(invoice["profiles"][PROFILE_NAME]["fields"]) == 2
    assert len(resolve_document_fields(invoice)) == 9
    assert set(invoice["collections"]) == {
        "services",
        "metering_points",
        "meters",
        "consumption_items",
    }
    assert invoice["collections"]["meters"]["start_pattern"]


def test_rejects_duplicate_field_names():
    invalid = copy.deepcopy(load_config())
    fields = get_profile_fields(invalid)
    fields.append(copy.deepcopy(fields[0]))
    with pytest.raises(ConfigValidationError, match="duplicate field name"):
        validate_config(invalid)


def test_rejects_invalid_regex():
    invalid = copy.deepcopy(load_config())
    find_common_field(invalid, "invoice_number")["rules"][0] = "("
    with pytest.raises(ConfigValidationError, match="invalid regex"):
        validate_config(invalid)


def test_rejects_unknown_field_type():
    invalid = copy.deepcopy(load_config())
    get_common_fields(invalid)[0]["type"] = "unknown_type"
    with pytest.raises(ConfigValidationError, match="is not supported"):
        validate_config(invalid)


def test_rejects_invalid_issue_date_regex():
    invalid = copy.deepcopy(load_config())
    find_common_field(invalid, "issue_date")["rules"][0] = "("
    with pytest.raises(ConfigValidationError, match="invalid regex"):
        validate_config(invalid)


def test_issue_date_has_before_and_after_rules():
    field = find_common_field(load_config(), "issue_date")
    assert field["type"] == "regex_list"
    assert len(field["rules"]) == 2


def test_rejects_unknown_default_profile():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["default_profile"] = "unknown_profile"
    with pytest.raises(ConfigValidationError, match="default_profile"):
        validate_config(invalid)


def test_rejects_duplicate_common_field():
    invalid = copy.deepcopy(load_config())
    fields = get_common_fields(invalid)
    fields.append(copy.deepcopy(fields[0]))
    with pytest.raises(ConfigValidationError, match="duplicate field name"):
        validate_config(invalid)


def test_rejects_invalid_collection_cardinality():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["collections"]["meters"]["cardinality"] = (
        "one_or_more"
    )
    with pytest.raises(ConfigValidationError, match="cardinality"):
        validate_config(invalid)


def test_rejects_unknown_collection_property():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["collections"]["meters"]["extractor"] = (
        "future"
    )
    with pytest.raises(
        ConfigValidationError,
        match="unsupported properties",
    ):
        validate_config(invalid)


def test_rejects_invalid_collection_start_pattern():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["collections"]["meters"]["start_pattern"] = "("
    with pytest.raises(ConfigValidationError, match="invalid regex"):
        validate_config(invalid)


def test_collection_start_pattern_is_optional():
    config = copy.deepcopy(load_config())
    config["invoice"]["collections"]["meters"].pop("start_pattern")
    validate_config(config)


def test_accepts_profile_collection_override():
    config = copy.deepcopy(load_config())
    profile = config["invoice"]["profiles"][
        "electricity_electrohold"
    ]

    assert "collections" in profile
    validate_config(config)


def test_rejects_invalid_profile_collection_start_pattern():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["start_pattern"] = "("

    with pytest.raises(ConfigValidationError, match="invalid regex"):
        validate_config(invalid)


def test_rejects_unknown_profile_collection_property():
    invalid = copy.deepcopy(load_config())
    invalid["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["meters"]["extractor"] = "future"

    with pytest.raises(
        ConfigValidationError,
        match="unsupported properties",
    ):
        validate_config(invalid)
