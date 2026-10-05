import pytest

from supplier_matcher import (
    SupplierMatcherError,
    SupplierMatchResult,
    match_supplier_from_config,
)


def synthetic_config():
    return {
        "profiles": {
            "synthetic_telecom": {
                "matching": {
                    "any_of": [
                        {
                            "code": "synthetic_company",
                            "pattern": r"\bsynthetic telecom ead\b",
                        },
                        {
                            "code": "synthetic_domain",
                            "pattern": r"(?<![\w.-])synthetic\.example(?![\w.-])",
                        },
                    ]
                },
                "fields": [],
            },
            "synthetic_energy": {
                "matching": {
                    "any_of": [
                        {
                            "code": "energy_company",
                            "pattern": r"\bsynthetic energy ead\b",
                        }
                    ]
                },
                "fields": [],
            },
            "profile_without_matching": {
                "fields": [],
            },
        }
    }


def test_selects_one_configured_profile_and_returns_all_evidence():
    result = match_supplier_from_config(
        synthetic_config(),
        "Synthetic Telecom EAD synthetic.example",
    )
    assert result == SupplierMatchResult(
        profile_name="synthetic_telecom",
        evidence=("synthetic_company", "synthetic_domain"),
    )


def test_matching_is_case_insensitive_and_normalizes_whitespace():
    result = match_supplier_from_config(
        synthetic_config(),
        "SYNTHETIC   TELECOM\nEAD",
    )
    assert result.profile_name == "synthetic_telecom"
    assert result.evidence == ("synthetic_company",)


def test_returns_unknown_when_no_profile_matches():
    assert match_supplier_from_config(
        synthetic_config(),
        "Unknown Supplier Ltd",
    ) == SupplierMatchResult(profile_name=None, evidence=())


def test_returns_ambiguous_when_multiple_profiles_match():
    result = match_supplier_from_config(
        synthetic_config(),
        "Synthetic Telecom EAD and Synthetic Energy EAD",
    )
    assert result.profile_name is None
    assert result.evidence == (
        "synthetic_company",
        "energy_company",
    )


def test_ignores_profiles_without_matching_rules():
    result = match_supplier_from_config(
        synthetic_config(),
        "profile_without_matching",
    )
    assert result == SupplierMatchResult(profile_name=None, evidence=())


def test_empty_text_returns_no_match():
    assert match_supplier_from_config(
        synthetic_config(),
        "  \n ",
    ) == SupplierMatchResult(profile_name=None, evidence=())


@pytest.mark.parametrize("invalid_config", [None, [], "invoice"])
def test_rejects_invalid_document_configuration(invalid_config):
    with pytest.raises(
        SupplierMatcherError,
        match="must be an object",
    ):
        match_supplier_from_config(invalid_config, "supplier")


def test_rejects_invalid_profiles_configuration():
    with pytest.raises(
        SupplierMatcherError,
        match="'profiles' must be an object",
    ):
        match_supplier_from_config({"profiles": []}, "supplier")


def test_legacy_matcher_remains_available():
    from supplier_matcher import match_supplier

    result = match_supplier("A1 Bulgaria EAD")
    assert result.profile_name == "telecom_a1"
