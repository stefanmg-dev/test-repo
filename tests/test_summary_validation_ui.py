from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "ui" / "test.html"
JS = ROOT / "ui" / "test.js"


def test_result_ui_has_separate_summary_validation_panel():
    html = HTML.read_text(encoding="utf-8")

    assert 'id="summaryValidationPanel"' in html
    assert 'id="summaryValidationBadge"' in html
    assert 'id="summaryValidationSummary"' in html
    assert 'id="summaryValidationErrors"' in html


def test_summary_validation_has_explicit_valid_and_invalid_states():
    content = JS.read_text(encoding="utf-8")

    assert "function renderSummaryValidation(summaryValidation)" in content
    assert '"SUMMARY VALID"' in content
    assert '"SUMMARY INVALID"' in content
    assert "renderSummaryValidation(" in content
    assert "body.summary_validation" in content


def test_summary_validation_errors_strip_internal_path_prefix():
    content = JS.read_text(encoding="utf-8")

    assert 'errorPath.startsWith("_summary.")' in content
    assert 'errorPath.slice("_summary.".length)' in content
    assert 'item.textContent = `${targetField}: ${message}`' in content


def test_summary_validation_is_separate_from_scalar_and_collection_errors():
    content = JS.read_text(encoding="utf-8")

    assert "elements.summaryValidationErrors.replaceChildren()" in content
    assert "renderValidationErrors(" in content
    assert "renderCollections(" in content
