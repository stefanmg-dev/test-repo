from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_JS = PROJECT_ROOT / "ui" / "test.js"


def read_test_javascript() -> str:
    return TEST_JS.read_text(
        encoding="utf-8"
    )


def test_testing_ui_reads_resolved_document_types():
    content = read_test_javascript()

    assert (
        "body?.resolved_document_types || {}"
        in content
    )


def test_testing_ui_has_resolved_state():
    content = read_test_javascript()

    assert "resolvedDocumentTypes: {}" in content


def test_field_labels_use_resolved_configuration():
    content = read_test_javascript()

    assert (
        "state.resolvedDocumentTypes["
        in content
    )


def test_rendered_fields_use_resolved_configuration():
    content = read_test_javascript()

    assert content.count(
        "state.resolvedDocumentTypes["
    ) >= 2