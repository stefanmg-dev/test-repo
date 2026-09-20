import copy

import pytest
from pydantic import ValidationError

from config_models import DocumentProfileModel
from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)
from document_config_resolver import (
    resolve_document_summary_validations,
)


PROFILE = "electricity_electrohold"


def summary_rule():
    return {
        "type": "collection_sum_equals_field",
        "collection": "consumption_items",
        "item_field": "quantity",
        "target_field": "total_consumption",
        "message": (
            "Consumption item quantities must equal "
            "total consumption"
        ),
    }


def get_profile(config):
    return config["invoice"]["profiles"][
        PROFILE
    ]


def test_validate_config_accepts_summary_rule():
    config = copy.deepcopy(load_config())

    get_profile(config)["summary_validations"] = [
        summary_rule()
    ]

    validate_config(config)


def test_validate_config_rejects_unknown_target_field():
    config = copy.deepcopy(load_config())
    validation = summary_rule()
    validation["target_field"] = "unknown_field"

    get_profile(config)["summary_validations"] = [
        validation
    ]

    with pytest.raises(
        ConfigValidationError,
        match="references unknown field",
    ):
        validate_config(config)


def test_validate_config_rejects_unknown_collection():
    config = copy.deepcopy(load_config())
    validation = summary_rule()
    validation["collection"] = "unknown_collection"

    get_profile(config)["summary_validations"] = [
        validation
    ]

    with pytest.raises(
        ConfigValidationError,
        match="references unknown collection",
    ):
        validate_config(config)


def test_validate_config_rejects_unknown_item_field():
    config = copy.deepcopy(load_config())
    validation = summary_rule()
    validation["item_field"] = "unknown_field"

    get_profile(config)["summary_validations"] = [
        validation
    ]

    with pytest.raises(
        ConfigValidationError,
        match="references unknown field",
    ):
        validate_config(config)


def test_profile_model_accepts_summary_rule():
    model = DocumentProfileModel.model_validate(
        {
            "fields": [],
            "collections": {},
            "summary_validations": [
                summary_rule()
            ],
        }
    )

    assert len(model.summary_validations) == 1


def test_profile_model_rejects_unsupported_rule():
    validation = summary_rule()
    validation["type"] = "unsupported_rule"

    with pytest.raises(ValidationError):
        DocumentProfileModel.model_validate(
            {
                "fields": [],
                "collections": {},
                "summary_validations": [
                    validation
                ],
            }
        )


def test_resolver_returns_profile_summary_rules():
    config = copy.deepcopy(load_config())

    get_profile(config)["summary_validations"] = [
        summary_rule()
    ]

    result = resolve_document_summary_validations(
        document_config=config["invoice"],
        profile_name=PROFILE,
    )

    assert result == [
        summary_rule()
    ]


@pytest.mark.parametrize(
    "profile_name",
    [
        None,
        "telecom_a1",
        "heating_toplofikacia_sofia",
    ],
)
def test_resolver_does_not_leak_summary_rules(
    profile_name,
):
    config = copy.deepcopy(load_config())

    get_profile(config)["summary_validations"] = [
        summary_rule()
    ]

    result = resolve_document_summary_validations(
        document_config=config["invoice"],
        profile_name=profile_name,
    )

    assert result == []
