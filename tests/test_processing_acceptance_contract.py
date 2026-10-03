from pathlib import Path

import pytest

from input_quality import assess_image_quality
from routes_extract import determine_processing_status


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "processing-acceptance-contract.md"
QUICK_REFERENCE = ROOT / "docs" / "development-quick-reference.md"


@pytest.mark.parametrize(
    (
        "scalar_valid",
        "collection_validation",
        "requires_review",
        "expected_status",
    ),
    [
        (True, None, False, "accepted"),
        (True, {"valid": True, "errors": {}}, False, "accepted"),
        (True, {"valid": True, "errors": {}}, True, "review"),
        (False, {"valid": True, "errors": {}}, False, "invalid"),
        (False, {"valid": True, "errors": {}}, True, "invalid"),
        (True, {"valid": False, "errors": {"x": ["bad"]}}, False, "invalid"),
        (True, {"valid": False, "errors": {"x": ["bad"]}}, True, "invalid"),
    ],
)
def test_processing_status_acceptance_matrix(
    scalar_valid,
    collection_validation,
    requires_review,
    expected_status,
):
    assert determine_processing_status(
        validation={"valid": scalar_valid, "errors": {}},
        quality={"requires_review": requires_review},
        collection_validation=collection_validation,
    ) == expected_status


def test_low_resolution_warning_is_stable_review_reason():
    quality = assess_image_quality(
        {
            "format": "JPEG",
            "width": 1000,
            "height": 1800,
            "short_edge": 1000,
            "long_edge": 1800,
            "pixel_count": 1800000,
            "mode": "RGB",
            "dpi": None,
        }
    )

    assert quality["status"] == "review"
    assert quality["requires_review"] is True
    assert quality["warnings"] == [
        {
            "code": "low_image_resolution",
            "message": (
                "Image resolution may be insufficient "
                "for reliable OCR"
            ),
        }
    ]


def test_acceptance_contract_documents_runtime_precedence():
    content = CONTRACT.read_text(encoding="utf-8")

    assert "Validation failure always has precedence" in content
    assert "`low_image_resolution`" in content
    assert "`validation.errors`" in content
    assert "`collection_validation.errors`" in content
    assert "`field_evidence[*].failure_reason`" in content
    assert "provider-specific acceptance rules" in content


def test_quick_reference_links_acceptance_contract():
    content = QUICK_REFERENCE.read_text(encoding="utf-8")
    assert "](processing-acceptance-contract.md)" in content
