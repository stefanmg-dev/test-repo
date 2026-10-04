from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "ui" / "test.html"
JS = ROOT / "ui" / "test.js"


def test_field_card_shows_final_llm_and_source_rows():
    html = HTML.read_text(encoding="utf-8")

    assert "Final стойност" in html
    assert "LLM стойност" in html
    assert "Източник" in html
    assert "field-final-value" in html
    assert "field-llm-value" in html
    assert "field-source-method" in html


def test_render_fields_receives_llm_values():
    content = JS.read_text(encoding="utf-8")

    signature = content[
        content.index("function renderFields("):
        content.index(") {", content.index("function renderFields(")) + 3
    ]
    assert "llmValues" in signature
    assert "body.llm_values || {}" in content


def test_field_comparison_uses_evidence_method_and_optional_llm_value():
    content = JS.read_text(encoding="utf-8")

    assert "Object.prototype.hasOwnProperty.call(" in content
    assert "llmValues[fieldName]" in content
    assert 'fieldEvidence?.method || "unknown"' in content
    assert '"Няма LLM стойност"' in content
    assert 'llmComparison.classList.toggle(' in content


def test_comparison_does_not_expose_sensitive_rule_metadata():
    content = JS.read_text(encoding="utf-8")

    assert "fieldEvidence.pattern" not in content
    assert "fieldEvidence.anchor;" not in content
    assert "fieldEvidence.value" not in content
