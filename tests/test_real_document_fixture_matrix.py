from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MATRIX = ROOT / "docs" / "real-document-fixture-matrix.md"
RUNNER = ROOT / "scripts" / "manual_invoice_regression.py"
QUICK_REFERENCE = ROOT / "docs" / "development-quick-reference.md"


def test_matrix_documents_all_existing_real_fixture_cases():
    content = MATRIX.read_text(encoding="utf-8")

    for case in (
        "A1 PDF",
        "A1 September PDF",
        "Electrohold PDF",
        "Toplofikacia PDF",
        "A1 JPEG variants",
        "Synthetic image-only PDF",
    ):
        assert case in content

    for variable in (
        "A1_REAL_PDF_PATH",
        "A1_SEPTEMBER_REAL_PDF_PATH",
        "ELECTROHOLD_REAL_PDF_PATH",
        "TOPLOFIKACIA_REAL_PDF_PATH",
        "A1_REAL_JPEG_DIR",
    ):
        assert variable in content


def test_matrix_defines_privacy_and_acceptance_boundaries():
    content = MATRIX.read_text(encoding="utf-8")

    assert "remains outside Git" in content
    assert "expected supplier profile" in content
    assert "Required scalar fields" in content
    assert "Required collections" in content
    assert "requires_review" in content
    assert "provider-independent defect" in content


def test_manual_runner_cases_are_represented_in_matrix():
    runner = RUNNER.read_text(encoding="utf-8")
    matrix = MATRIX.read_text(encoding="utf-8")

    for filename in (
        "a1.pdf",
        "a1-september.pdf",
        "electrohold.pdf",
        "toplofikacia.pdf",
    ):
        assert filename in runner
        assert filename in matrix


def test_quick_reference_links_fixture_matrix():
    content = QUICK_REFERENCE.read_text(encoding="utf-8")
    assert "](real-document-fixture-matrix.md)" in content
