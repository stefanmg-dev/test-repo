import pytest
from pydantic import ValidationError

from config_models import DocumentProfileModel
from config_validator import ConfigValidationError, validate_config


def matching_config():
    return {
        "any_of": [
            {
                "code": "synthetic_provider_company",
                "pattern": r"\bsynthetic provider ead\b",
            },
            {
                "code": "synthetic_provider_domain",
                "pattern": r"(?<![\w.-])synthetic\.example(?![\w.-])",
            },
        ]
    }


def document_config(matching):
    return {
        "invoice": {
            "default_profile": "synthetic_provider",
            "common_fields": [],
            "profiles": {
                "synthetic_provider": {
                    "matching": matching,
                    "fields": [],
                }
            },
        }
    }


def test_profile_model_accepts_supplier_matching_contract():
    model = DocumentProfileModel.model_validate(
        {"matching": matching_config(), "fields": []}
    )
    assert [rule.code for rule in model.matching.any_of] == [
        "synthetic_provider_company",
        "synthetic_provider_domain",
    ]


def test_config_validator_accepts_supplier_matching_contract():
    validate_config(document_config(matching_config()))


@pytest.mark.parametrize(
    "matching",
    [
        {"any_of": []},
        {"any_of": [{"code": "Invalid Code", "pattern": "valid"}]},
        {"any_of": [{"code": "valid_code", "pattern": "("}]},
        {
            "any_of": [
                {"code": "duplicate", "pattern": "first"},
                {"code": "duplicate", "pattern": "second"},
            ]
        },
        {"all_of": [{"code": "valid_code", "pattern": "valid"}]},
    ],
)
def test_profile_model_rejects_invalid_supplier_matching(matching):
    with pytest.raises(ValidationError):
        DocumentProfileModel.model_validate(
            {"matching": matching, "fields": []}
        )


@pytest.mark.parametrize(
    "matching",
    [
        {"any_of": []},
        {"any_of": [{"code": "Invalid Code", "pattern": "valid"}]},
        {"any_of": [{"code": "valid_code", "pattern": "("}]},
        {
            "any_of": [
                {"code": "duplicate", "pattern": "first"},
                {"code": "duplicate", "pattern": "second"},
            ]
        },
        {"all_of": [{"code": "valid_code", "pattern": "valid"}]},
    ],
)
def test_config_validator_rejects_invalid_supplier_matching(matching):
    with pytest.raises(ConfigValidationError):
        validate_config(document_config(matching))
