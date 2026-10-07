from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNNER = PROJECT_ROOT / "scripts" / "manual_invoice_regression.py"
A1_TEST = PROJECT_ROOT / "tests" / "test_a1_real_pdf_e2e.py"


def test_manual_regression_runner_suppresses_test_output():
    content = RUNNER.read_text(encoding="utf-8")

    assert "stdout=subprocess.DEVNULL" in content
    assert "stderr=subprocess.DEVNULL" in content
    assert "final_values" not in content
    assert "raw_text" not in content


def test_manual_regression_runner_uses_ignored_fixture_paths():
    content = RUNNER.read_text(encoding="utf-8")

    assert '"uploaded_documents" / "manual-regression"' in content
    assert '"a1.pdf"' in content
    assert '"electrohold.pdf"' in content
    assert '"toplofikacia.pdf"' in content


def test_a1_real_pdf_test_does_not_assert_personal_values():
    content = A1_TEST.read_text(encoding="utf-8")

    assert '"profile"] == "telecom_a1"' in content
    assert 'set(final_values) == expected_field_names' in content
    assert 'value not in {None, ""}' in content
    assert 'quality["status"] == "accepted"' in content
    assert 'quality["requires_review"] is False' in content
    assert '"unknown_supplier_profile" not in warning_codes' in content
    assert "customer_name" not in content
    assert "customer_address" not in content
    assert "invoice_number" not in content
    assert "contract_number" not in content
