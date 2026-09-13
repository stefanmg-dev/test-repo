from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_JS = PROJECT_ROOT / "ui" / "ui.js"
INDEX_HTML = PROJECT_ROOT / "ui" / "index.html"


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_configuration_ui_tracks_resolved_document_types():
    content = read_text(UI_JS)

    assert "resolvedDocumentTypes: {}" in content

    assert (
        "response.resolved_document_types || {}"
        in content
    )


def test_configuration_ui_tracks_selected_field_scope():
    content = read_text(UI_JS)

    assert "selectedFieldScope" in content
    assert "common" in content
    assert "profile" in content


def test_configuration_ui_reads_common_fields():
    content = read_text(UI_JS)

    assert "config.common_fields || []" in content


def test_configuration_ui_reads_profile_fields():
    content = read_text(UI_JS)

    assert "config.profiles" in content
    assert "config.default_profile" in content


def test_configuration_ui_uses_common_field_endpoint():
    content = read_text(UI_JS)

    assert "/common-fields" in content


def test_configuration_ui_uses_profile_field_endpoint():
    content = read_text(UI_JS)

    assert "/profiles/" in content


def test_configuration_page_contains_field_scope_control():
    content = read_text(INDEX_HTML)

    assert 'id="fieldScope"' in content


def test_configuration_page_contains_profile_information():
    content = read_text(INDEX_HTML)

    assert 'id="selectedProfileName"' in content
    assert 'id="fieldScopeSection"' in content