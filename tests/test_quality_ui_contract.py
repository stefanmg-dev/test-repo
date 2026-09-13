from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_HTML = PROJECT_ROOT / "ui" / "test.html"
TEST_JS = PROJECT_ROOT / "ui" / "test.js"


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_testing_page_contains_quality_elements():
    content = read_text(TEST_HTML)

    assert 'id="qualitySection"' in content
    assert 'id="qualityBadge"' in content
    assert 'id="qualitySummary"' in content
    assert 'id="qualityWarnings"' in content
    assert 'id="qualityDetails"' in content


def test_testing_javascript_reads_quality_response():
    content = read_text(TEST_JS)

    assert "body.quality" in content
    assert "renderInputQuality" in content
    assert "quality.requires_review" in content
    assert "quality.warnings" in content


def test_testing_javascript_renders_input_dimensions():
    content = read_text(TEST_JS)

    assert "quality.input" in content
    assert "input.width" in content
    assert "input.height" in content
    assert "input.format" in content


def test_quality_is_separate_from_validation():
    content = read_text(TEST_JS)

    assert "renderInputQuality" in content
    assert "renderValidationErrors" in content
    assert "renderResult" in content

def test_testing_page_contains_profile_diagnostic():
    html_content = read_text(TEST_HTML)
    js_content = read_text(TEST_JS)

    assert (
        'id="diagnosticProfile"'
        in html_content
    )

    assert (
        "body.profile"
        in js_content
    )

    assert (
        "diagnosticProfile"
        in js_content
    )