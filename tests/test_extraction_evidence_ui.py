from pathlib import Path


UI = (
    Path(__file__).resolve().parent.parent
    / "ui"
    / "test.js"
)


def test_extraction_result_renders_field_evidence():
    content = UI.read_text(encoding="utf-8")

    assert "body.field_evidence || {}" in content
    assert "evidence?.[fieldName]" in content
    assert "fieldEvidence.method" in content
    assert "fieldEvidence.matched" in content
    assert "fieldEvidence.normalized" in content
    assert "fieldEvidence.rule_index + 1" in content
    assert "fieldEvidence.failure_reason" in content


def test_field_evidence_rendering_does_not_use_sensitive_metadata():
    content = UI.read_text(encoding="utf-8")

    assert "fieldEvidence.pattern" not in content
    assert "fieldEvidence.anchor_found" in content
    assert "fieldEvidence.anchor;" not in content
    assert "fieldEvidence.value" not in content
