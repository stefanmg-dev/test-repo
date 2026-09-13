import pytest
from pydantic import ValidationError

from config_models import DocumentTypeModel
from config_validator import (
    ConfigValidationError,
    validate_config,
)


def build_profile_config(
    default_profile="telecom_a1",
):
    return {
        "invoice": {
            "default_profile": default_profile,
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
                            "rule": (
                                "([МM][0-9]+)"
                            ),
                        }
                    ]
                },
                "electricity_evn": {
                    "fields": [
                        {
                            "name": "customer_number",
                            "type": "regex",
                            "rule": "([0-9]+)",
                        }
                    ]
                },
            },
        }
    }


def test_model_accepts_existing_default_profile():
    document_config = build_profile_config()[
        "invoice"
    ]

    model = DocumentTypeModel.model_validate(
        document_config
    )

    assert model.default_profile == (
        "telecom_a1"
    )

    assert "telecom_a1" in model.profiles


def test_model_rejects_unknown_default_profile():
    document_config = build_profile_config(
        default_profile="unknown_profile"
    )["invoice"]

    with pytest.raises(
        ValidationError,
        match="default_profile",
    ):
        DocumentTypeModel.model_validate(
            document_config
        )


def test_model_rejects_default_profile_with_legacy_fields():
    document_config = {
        "fields": [],
        "default_profile": "telecom_a1",
    }

    with pytest.raises(
        ValidationError,
        match="default_profile",
    ):
        DocumentTypeModel.model_validate(
            document_config
        )


def test_validator_accepts_existing_default_profile():
    validate_config(
        build_profile_config()
    )


def test_validator_rejects_unknown_default_profile():
    config = build_profile_config(
        default_profile="unknown_profile"
    )

    with pytest.raises(
        ConfigValidationError,
        match="default_profile",
    ):
        validate_config(config)


def test_validator_rejects_invalid_default_profile_name():
    config = build_profile_config(
        default_profile="Telecom A1"
    )

    with pytest.raises(
        ConfigValidationError,
        match="default_profile",
    ):
        validate_config(config)


def test_validator_rejects_non_string_default_profile():
    config = build_profile_config(
        default_profile=123
    )

    with pytest.raises(
        ConfigValidationError,
        match="default_profile",
    ):
        validate_config(config)


def test_validator_rejects_default_profile_with_legacy_fields():
    config = {
        "invoice": {
            "fields": [],
            "default_profile": "telecom_a1",
        }
    }

    with pytest.raises(
        ConfigValidationError,
        match="default_profile",
    ):
        validate_config(config)
