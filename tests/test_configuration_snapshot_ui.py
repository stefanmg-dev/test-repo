from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "ui" / "index.html"
UI_JS = ROOT / "ui" / "ui.js"


def test_configuration_ui_contains_snapshot_export_action():
    html = INDEX.read_text(encoding="utf-8")
    javascript = UI_JS.read_text(encoding="utf-8")

    assert 'id="navExportConfiguration"' in html
    assert "Експортирай конфигурацията" in html
    assert 'navExportConfiguration: byId("navExportConfiguration")' in javascript
    assert 'apiRequest("/snapshot")' in javascript


def test_configuration_ui_downloads_versioned_snapshot_json():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "JSON.stringify(snapshot, null, 2)" in javascript
    assert "new Blob([content]" in javascript
    assert "URL.createObjectURL(blob)" in javascript
    assert "configuration-${snapshot.revision}.json" in javascript
    assert "URL.revokeObjectURL(url)" in javascript


def test_configuration_ui_reports_export_result():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "Конфигурацията е експортирана." in javascript
    assert "Грешка при експортиране:" in javascript
