from pathlib import Path


JS = Path(__file__).resolve().parent.parent / "ui" / "test.js"


def test_collection_evidence_is_rendered_as_structured_details():
    content = JS.read_text(encoding="utf-8")

    assert "collection-evidence-details" in content
    assert '"Extraction method"' in content
    assert '"Match status"' in content
    assert '"Normalization"' in content
    assert '"Failure reason"' in content


def test_collection_validation_errors_are_visually_separate():
    content = JS.read_text(encoding="utf-8")

    assert "const fieldErrors = [" in content
    assert '`Validation: ${fieldErrors.join("; ")}`' in content
    assert 'diagnostics.style.color = "#b91c1c"' in content


def test_collection_evidence_preserves_optional_diagnostics():
    content = JS.read_text(encoding="utf-8")

    assert "evidence.occurrence" in content
    assert "evidence.rule_index !== undefined" in content
    assert "evidence.rule_index + 1" in content
    assert "evidence.failure_reason" in content


def test_collection_evidence_does_not_expose_sensitive_metadata():
    content = JS.read_text(encoding="utf-8")

    assert "evidence.pattern" not in content
    assert "evidence.anchor" not in content
    assert "evidence.value" not in content
