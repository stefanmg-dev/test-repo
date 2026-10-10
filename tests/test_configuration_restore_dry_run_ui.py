from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "ui" / "index.html"
UI_JS = ROOT / "ui" / "ui.js"


def test_configuration_ui_contains_restore_dry_run_controls():
    html = INDEX.read_text(encoding="utf-8")
    javascript = UI_JS.read_text(encoding="utf-8")

    assert 'id="navValidateRestore"' in html
    assert "Провери snapshot" in html
    assert 'id="restoreSnapshotInput"' in html
    assert 'type="file"' in html
    assert 'accept="application/json,.json"' in html
    assert 'navValidateRestore: byId("navValidateRestore")' in javascript
    assert 'restoreSnapshotInput: byId("restoreSnapshotInput")' in javascript


def test_configuration_ui_reads_and_validates_snapshot():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "JSON.parse(await file.text())" in javascript
    assert 'apiRequest("/restore/dry-run"' in javascript
    assert 'method: "POST"' in javascript
    assert "body: JSON.stringify(snapshot)" in javascript


def test_configuration_ui_reports_dry_run_result_and_errors():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "result.changes_detected" in javascript
    assert "result.snapshot_revision" in javascript
    assert "result.current_revision" in javascript
    assert 'result.document_types.join(", ")' in javascript
    assert "Snapshot е валиден:" in javascript
    assert "Невалиден snapshot:" in javascript
