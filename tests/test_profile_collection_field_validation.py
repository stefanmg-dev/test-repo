import copy

import pytest
from pydantic import ValidationError

from config_models import DocumentCollectionModel
from config_store import load_config
from config_validator import (
    ConfigValidationError,
    validate_config,
)


PROFILE_NAME = "heating_toplofikacia_sofia"
COLLECTION_NAME = "services"


def get_services_schema(config):
    return config["invoice"]["profiles"][
        PROFILE_NAME
    ]["collections"][COLLECTION_NAME]


def test_rejects_duplicate_profile_collection_field_name():
    config = copy.deepcopy(load_config())
    services = get_services_schema(config)

    duplicate = copy.deepcopy(services["fields"][0])
    services["fields"].append(duplicate)

    with pytest.raises(
        ConfigValidationError,
        match=(
            r"document_types\.invoice\.profiles\."
            r"heating_toplofikacia_sofia\.collections\."
            r"services\.fields\[[0-9]+\]\.name "
            r"contains duplicate field name"
        ),
    ):
        validate_config(config)


def test_rejects_unsupported_profile_collection_field_type():
    config = copy.deepcopy(load_config())
    services = get_services_schema(config)

    services["fields"][0]["type"] = "unsupported_type"

    with pytest.raises(
        ConfigValidationError,
        match=(
            r"document_types\.invoice\.profiles\."
            r"heating_toplofikacia_sofia\.collections\."
            r"services\.fields\[0\]\.type "
            r"'unsupported_type' is not supported"
        ),
    ):
        validate_config(config)


def test_rejects_invalid_profile_collection_field_regex():
    config = copy.deepcopy(load_config())
    services = get_services_schema(config)

    services["fields"][0]["type"] = "regex"
    services["fields"][0]["rule"] = "("

    with pytest.raises(
        ConfigValidationError,
        match="invalid regex",
    ):
        validate_config(config)


def test_collection_model_rejects_duplicate_field_names():
    with pytest.raises(
        ValidationError,
        match="Duplicate collection field",
    ):
        DocumentCollectionModel.model_validate(
            {
                "cardinality": "zero_or_more",
                "fields": [
                    {
                        "name": "amount",
                        "type": "constant",
                        "value": "1.00",
                    },
                    {
                        "name": "amount",
                        "type": "constant",
                        "value": "2.00",
                    },
                ],
            }
        )


def test_collection_model_rejects_unsupported_field_type():
    with pytest.raises(ValidationError):
        DocumentCollectionModel.model_validate(
            {
                "cardinality": "zero_or_more",
                "fields": [
                    {
                        "name": "amount",
                        "type": "unsupported_type",
                    }
                ],
            }
        )
