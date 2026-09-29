from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_HTML = PROJECT_ROOT / "ui" / "test.html"
TEST_JS = PROJECT_ROOT / "ui" / "test.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_testing_ui_controls_reference_visible_instructions():
    content = read(TEST_HTML)

    assert 'aria-describedby="documentTypeHelp"' in content
    assert 'id="documentTypeHelp"' in content
    assert 'aria-describedby="documentFileHelp"' in content
    assert 'id="documentFileHelp"' in content
    assert "PDF, JPG, JPEG или PNG" in content


def test_testing_ui_status_regions_are_programmatically_announced():
    content = read(TEST_HTML)

    assert 'id="messageArea"' in content
    assert 'role="status"' in content
    assert 'aria-live="polite"' in content
    assert 'aria-atomic="true"' in content
    assert 'id="processingSection"' in content


def test_testing_ui_errors_use_alert_semantics():
    content = read(TEST_JS)

    assert 'type === "error" ? "alert" : "status"' in content
    assert 'type === "error" ? "assertive" : "polite"' in content
    assert 'box.setAttribute("role", "alert")' in content
    assert 'box.setAttribute("aria-atomic", "true")' in content


def test_testing_ui_clear_message_restores_polite_status_semantics():
    content = read(TEST_JS)

    assert '"role",' in content
    assert '"status"' in content
    assert '"aria-live",' in content
    assert '"polite"' in content
