from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIGURATION_UI_JS = PROJECT_ROOT / "ui" / "ui.js"
EXTRACTION_UI_JS = PROJECT_ROOT / "ui" / "test.js"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_extraction_ui_uses_backend_metadata():
    content = read_text(EXTRACTION_UI_JS)

    assert "documentTypeMetadata" in content
    assert "document_type_metadata" in content
    assert "metadata?.ready === true" in content
    assert "metadata.field_count" in content


def test_configuration_ui_uses_backend_metadata():
    content = read_text(CONFIGURATION_UI_JS)

    assert "documentTypeMetadata" in content
    assert "document_type_metadata" in content
    assert "metadata.status" in content
    assert "metadata.field_count" in content
