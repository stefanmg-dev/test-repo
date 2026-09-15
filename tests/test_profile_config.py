import pytest
from pydantic import ValidationError

from config_models import DocumentTypeModel
from config_validator import ConfigValidationError, validate_config


def profile_config():
    return {
        "invoice": {
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
                            "rule": "([МM][0-9]+)",
                        }
                    ]
                }
            },
        }
    }


def test_profile_document_model_is_valid():
    model = DocumentTypeModel.model_validate(profile_config()["invoice"])
    assert len(model.common_fields) == 1
    assert "telecom_a1" in model.profiles


def test_legacy_document_model_remains_valid():
    model = DocumentTypeModel.model_validate({"fields": []})
    assert model.fields == []


def test_model_rejects_mixed_shapes():
    with pytest.raises(ValidationError):
        DocumentTypeModel.model_validate(
            {"fields": [], "common_fields": [], "profiles": {}}
        )


def test_validator_accepts_profile_configuration():
    validate_config(profile_config())


def test_validator_rejects_mixed_shapes():
    config = profile_config()
    config["invoice"]["fields"] = []

    with pytest.raises(ConfigValidationError, match="cannot combine"):
        validate_config(config)


def test_validator_accepts_common_field_override():
    config = profile_config()

    config["invoice"]["profiles"]["telecom_a1"][
        "fields"
    ][0]["name"] = "invoice_number"

    validate_config(config)


def test_validator_rejects_duplicate_profile_field():
    config = profile_config()

    duplicate_field = dict(
        config["invoice"]["profiles"][
            "telecom_a1"
        ]["fields"][0]
    )

    config["invoice"]["profiles"][
        "telecom_a1"
    ]["fields"].append(
        duplicate_field
    )

    with pytest.raises(
        ConfigValidationError,
        match="duplicate field name",
    ):
        validate_config(config)


def test_validator_rejects_invalid_profile_name():
    config = profile_config()
    config["invoice"]["profiles"]["Telecom A1"] = config["invoice"][
        "profiles"
    ].pop("telecom_a1")

    with pytest.raises(ConfigValidationError, match="must match"):
        validate_config(config)


def test_validator_rejects_invalid_profile_field_rule():
    config = profile_config()
    config["invoice"]["profiles"]["telecom_a1"]["fields"][0]["rule"] = "("

    with pytest.raises(ConfigValidationError, match="invalid regex"):
        validate_config(config)
