import copy

import pytest

from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)


def test_current_document_types_config_is_valid():
    config = load_config()

    assert "invoice" in config
    assert len(config["invoice"]["fields"]) == 9


def test_rejects_duplicate_field_names():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    duplicate_field = copy.deepcopy(
        invalid_config["invoice"]["fields"][0]
    )

    invalid_config["invoice"]["fields"].append(
        duplicate_field
    )

    with pytest.raises(
        ConfigValidationError,
        match="duplicate field name",
    ):
        validate_config(invalid_config)


def test_rejects_invalid_regex():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    invoice_number_field = next(
        field
        for field in invalid_config["invoice"]["fields"]
        if field["name"] == "invoice_number"
    )

    invoice_number_field["rules"][0] = "("

    with pytest.raises(
        ConfigValidationError,
        match="invalid regex",
    ):
        validate_config(invalid_config)


def test_rejects_unknown_field_type():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    invalid_config["invoice"]["fields"][0]["type"] = (
        "unknown_type"
    )

    with pytest.raises(
        ConfigValidationError,
        match="is not supported",
    ):
        validate_config(invalid_config)


def test_rejects_invalid_nearby_direction():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    issue_date_field = next(
        field
        for field in invalid_config["invoice"]["fields"]
        if field["name"] == "issue_date"
    )

    assert issue_date_field["type"] == "nearby"

    issue_date_field["direction"] = "sideways"

    with pytest.raises(
        ConfigValidationError,
        match="direction",
    ):
        validate_config(invalid_config)


def test_rejects_invalid_window_size():
    config = load_config()
    invalid_config = copy.deepcopy(config)

    issue_date_field = next(
        field
        for field in invalid_config["invoice"]["fields"]
        if field["name"] == "issue_date"
    )

    assert issue_date_field["type"] == "nearby"

    issue_date_field["window_size"] = 0

    with pytest.raises(
        ConfigValidationError,
        match="positive integer",
    ):
        validate_config(invalid_config)
