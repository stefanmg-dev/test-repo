import copy

import pytest
from pydantic import ValidationError

from config_models import DocumentCollectionModel
from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)


PROFILE = "electricity_electrohold"
COLLECTION = "consumption_items"


def difference_rule():
    return {
        "type": "difference_equals",
        "minuend": "current_reading",
        "subtrahend": "previous_reading",
        "result": "difference",
        "message": (
            "Difference must equal current reading "
            "minus previous reading"
        ),
    }


def profile_schema(config):
    return config["invoice"]["profiles"][
        PROFILE
    ]["collections"][COLLECTION]


def test_validate_config_accepts_difference_equals():
    config = copy.deepcopy(load_config())

    profile_schema(config)["item_validations"] = [
        difference_rule()
    ]

    validate_config(config)


def test_validate_config_rejects_unknown_reference():
    config = copy.deepcopy(load_config())
    rule = difference_rule()
    rule["result"] = "unknown_field"

    profile_schema(config)["item_validations"] = [
        rule
    ]

    with pytest.raises(
        ConfigValidationError,
        match="references unknown field",
    ):
        validate_config(config)


def test_validate_config_rejects_unsupported_rule():
    config = copy.deepcopy(load_config())
    rule = difference_rule()
    rule["type"] = "unsupported_rule"

    profile_schema(config)["item_validations"] = [
        rule
    ]

    with pytest.raises(
        ConfigValidationError,
        match="must be one of",
    ):
        validate_config(config)


def test_collection_model_accepts_difference_equals():
    model = DocumentCollectionModel.model_validate(
        {
            "fields": [
                {
                    "name": "previous_reading",
                    "type": "constant",
                    "value": "10",
                },
                {
                    "name": "current_reading",
                    "type": "constant",
                    "value": "20",
                },
                {
                    "name": "difference",
                    "type": "constant",
                    "value": "10",
                },
            ],
            "item_validations": [
                difference_rule()
            ],
        }
    )

    assert len(model.item_validations) == 1


def test_collection_model_rejects_unknown_reference():
    rule = difference_rule()
    rule["result"] = "unknown_field"

    with pytest.raises(
        ValidationError,
        match="references unknown fields",
    ):
        DocumentCollectionModel.model_validate(
            {
                "fields": [
                    {
                        "name": "previous_reading",
                        "type": "constant",
                        "value": "10",
                    },
                    {
                        "name": "current_reading",
                        "type": "constant",
                        "value": "20",
                    },
                    {
                        "name": "difference",
                        "type": "constant",
                        "value": "10",
                    },
                ],
                "item_validations": [
                    rule
                ],
            }
        )
