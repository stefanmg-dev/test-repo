from supplier_profile_pipeline import (
    has_configured_supplier_matching,
    resolve_supplier_profile_fields,
)


COMMON_FIELD = {
    "name": "invoice_number",
    "type": "text",
}
SYNTHETIC_FIELD = {
    "name": "synthetic_account",
    "type": "text",
}
OTHER_FIELD = {
    "name": "other_account",
    "type": "text",
}


def configured_document():
    return {
        "default_profile": "synthetic_provider",
        "common_fields": [COMMON_FIELD],
        "profiles": {
            "synthetic_provider": {
                "matching": {
                    "any_of": [
                        {
                            "code": "synthetic_company",
                            "pattern": r"\bsynthetic provider ead\b",
                        }
                    ]
                },
                "fields": [SYNTHETIC_FIELD],
            },
            "other_provider": {
                "matching": {
                    "any_of": [
                        {
                            "code": "other_company",
                            "pattern": r"\bother provider ead\b",
                        }
                    ]
                },
                "fields": [OTHER_FIELD],
            },
        },
    }


def test_detects_configured_supplier_matching():
    assert has_configured_supplier_matching(configured_document()) is True
    assert has_configured_supplier_matching(
        {"profiles": {"legacy": {"fields": []}}}
    ) is False


def test_pipeline_selects_profile_from_configuration():
    result = resolve_supplier_profile_fields(
        document_config=configured_document(),
        ocr_text="Supplier: Synthetic Provider EAD",
    )
    assert result == {
        "profile": "synthetic_provider",
        "fields": [COMMON_FIELD, SYNTHETIC_FIELD],
        "requires_review": False,
        "warnings": [],
        "supplier_evidence": ["synthetic_company"],
    }


def test_pipeline_uses_common_only_for_unknown_configured_supplier():
    result = resolve_supplier_profile_fields(
        document_config=configured_document(),
        ocr_text="Unknown Provider Ltd",
    )
    assert result["profile"] is None
    assert result["fields"] == [COMMON_FIELD]
    assert result["requires_review"] is True
    assert result["supplier_evidence"] == []


def test_pipeline_uses_common_only_for_ambiguous_configured_supplier():
    result = resolve_supplier_profile_fields(
        document_config=configured_document(),
        ocr_text=(
            "Synthetic Provider EAD and Other Provider EAD"
        ),
    )
    assert result["profile"] is None
    assert result["fields"] == [COMMON_FIELD]
    assert result["requires_review"] is True
    assert result["supplier_evidence"] == [
        "synthetic_company",
        "other_company",
    ]


def test_configured_matching_is_authoritative_over_legacy_matcher():
    result = resolve_supplier_profile_fields(
        document_config=configured_document(),
        ocr_text="A1 Bulgaria EAD",
    )
    assert result["profile"] is None
    assert result["fields"] == [COMMON_FIELD]
    assert result["requires_review"] is True


def test_pipeline_preserves_legacy_matcher_without_matching_config():
    legacy_config = {
        "default_profile": "telecom_a1",
        "common_fields": [COMMON_FIELD],
        "profiles": {
            "telecom_a1": {
                "fields": [SYNTHETIC_FIELD],
            }
        },
    }
    result = resolve_supplier_profile_fields(
        document_config=legacy_config,
        ocr_text="A1 Bulgaria EAD",
    )
    assert result["profile"] == "telecom_a1"
    assert result["fields"] == [COMMON_FIELD, SYNTHETIC_FIELD]
    assert result["requires_review"] is False
