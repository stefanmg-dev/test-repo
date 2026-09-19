import copy

import pytest
from pydantic import ValidationError

from config_models import DocumentCollectionModel
from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)


def test_validate_config_rejects_invalid_global_cardinality():
    config = copy.deepcopy(load_config())

    config["invoice"]["collections"]["services"][
        "cardinality"
    ] = "one_or_mroe"

    with pytest.raises(
        ConfigValidationError,
        match=(
            r"document_types\.invoice\.collections\.services"
            r"\.cardinality must be one of:"
        ),
    ):
        validate_config(config)


def test_validate_config_rejects_invalid_profile_cardinality():
    config = copy.deepcopy(load_config())

    config["invoice"]["profiles"][
        "heating_toplofikacia_sofia"
    ]["collections"]["services"]["cardinality"] = (
        "one_or_mroe"
    )

    with pytest.raises(
        ConfigValidationError,
        match=(
            r"document_types\.invoice\.profiles"
            r"\.heating_toplofikacia_sofia\.collections"
            r"\.services\.cardinality must be one of:"
        ),
    ):
        validate_config(config)


@pytest.mark.parametrize(
    "cardinality",
    [
        "zero_or_more",
        "one_or_more",
        "exactly_one",
    ],
)
def test_collection_model_accepts_supported_cardinalities(
    cardinality,
):
    model = DocumentCollectionModel.model_validate(
        {
            "cardinality": cardinality,
            "fields": [],
        }
    )

    assert model.cardinality == cardinality


def test_collection_model_rejects_invalid_cardinality():
    with pytest.raises(ValidationError):
        DocumentCollectionModel.model_validate(
            {
                "cardinality": "one_or_mroe",
                "fields": [],
            }
        )


def test_collection_model_defaults_to_zero_or_more():
    model = DocumentCollectionModel.model_validate(
        {
            "fields": [],
        }
    )

    assert model.cardinality == "zero_or_more"
