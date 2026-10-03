from pathlib import Path
from types import SimpleNamespace

import pytest

from processing_run_service import ProcessingRunReviewService


ROOT = Path(__file__).resolve().parent.parent
CONTRACT = ROOT / "docs" / "human-review-acceptance-contract.md"
QUICK_REFERENCE = ROOT / "docs" / "development-quick-reference.md"


@pytest.mark.parametrize(
    ("status", "corrected_values", "expected"),
    [
        ("pending", None, {"invoice_number": "ORIGINAL"}),
        ("approved", None, {"invoice_number": "ORIGINAL"}),
        ("corrected", {"invoice_number": "CORRECTED"}, {"invoice_number": "CORRECTED"}),
        ("rejected", None, None),
    ],
)
def test_effective_value_acceptance_matrix(
    status,
    corrected_values,
    expected,
):
    run = SimpleNamespace(
        review_status=status,
        final_values={"invoice_number": "ORIGINAL"},
        corrected_values=corrected_values,
    )

    assert ProcessingRunReviewService.effective_values(run) == expected


def test_review_contract_documents_terminal_decisions_and_audit():
    content = CONTRACT.read_text(encoding="utf-8")

    for decision in ("`approved`", "`corrected`", "`rejected`"):
        assert decision in content

    assert "Every decision is terminal" in content
    assert "Original `final_values`" in content
    assert "recorded atomically" in content
    assert "processing-runs:review" in content
    assert "Tenant isolation" in content
    assert "concurrent terminal decisions" in content


def test_review_contract_defines_corrected_value_boundaries():
    content = CONTRACT.read_text(encoding="utf-8")

    assert "Corrected values are rejected" in content
    assert "corrected review requires" in content
    assert "rejected review returns no effective values" in content


def test_quick_reference_links_review_contract():
    content = QUICK_REFERENCE.read_text(encoding="utf-8")
    assert "](human-review-acceptance-contract.md)" in content
