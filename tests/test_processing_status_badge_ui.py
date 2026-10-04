from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
HTML = ROOT / "ui" / "test.html"
JS = ROOT / "ui" / "test.js"


def test_result_header_has_separate_processing_and_validation_badges():
    html = HTML.read_text(encoding="utf-8")

    assert 'id="processingStatusBadge"' in html
    assert 'id="validationBadge"' in html
    assert "VALIDATION UNKNOWN" in html


def test_processing_status_badge_has_three_explicit_states():
    content = JS.read_text(encoding="utf-8")

    assert "function renderProcessingStatus(status)" in content
    assert 'label: "ACCEPTED"' in content
    assert 'label: "REVIEW"' in content
    assert 'label: "INVALID"' in content
    assert "renderProcessingStatus(body.processing_status)" in content


def test_review_status_uses_warning_not_error_message_style():
    content = JS.read_text(encoding="utf-8")

    review_start = content.index('if (status === "review")')
    review_end = content.index(
        "\n    return {",
        review_start,
    )
    review_block = content[review_start:review_end]

    assert 'type: "warning"' in review_block
    assert 'type: "error"' not in review_block


def test_scalar_validation_badge_remains_separate():
    content = JS.read_text(encoding="utf-8")

    assert '"VALIDATION VALID"' in content
    assert '"VALIDATION INVALID"' in content
