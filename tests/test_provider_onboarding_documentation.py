from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ONBOARDING = ROOT / "docs" / "provider-onboarding.md"
CONFIG_GUIDE = ROOT / "docs" / "configuration-guide.md"
FIXTURE_MATRIX = ROOT / "docs" / "real-document-fixture-matrix.md"
QUICK_REFERENCE = ROOT / "docs" / "development-quick-reference.md"


def test_provider_onboarding_document_exists_and_defines_core_contract():
    content = ONBOARDING.read_text(encoding="utf-8")
    for required in (
        "matching.any_of",
        "profile=None",
        "ambiguous multi-supplier",
        "provider-specific runtime Python code",
        "common fields",
        "profile fields",
        "Real-document acceptance",
        "Full `pytest`",
        "Alembic",
        "supply-chain security",
        "document_types.json",
    ):
        assert required in content


def test_provider_onboarding_requires_privacy_and_regression_safety():
    content = ONBOARDING.read_text(encoding="utf-8")
    assert "outside Git" in content
    assert "sensitive document content" in content
    assert "existing provider baselines remain green" in content
    assert "unknown supplier behavior remains common-only review" in content


def test_provider_onboarding_is_linked_from_core_guides():
    expected = "[Provider onboarding](provider-onboarding.md)"
    assert expected in CONFIG_GUIDE.read_text(encoding="utf-8")
    assert expected in FIXTURE_MATRIX.read_text(encoding="utf-8")
    assert expected in QUICK_REFERENCE.read_text(encoding="utf-8")
