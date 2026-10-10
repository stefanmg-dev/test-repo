from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "ui" / "index.html"
UI_JS = ROOT / "ui" / "ui.js"


def test_guarded_restore_ui_is_hidden_until_changed_dry_run():
    html = INDEX.read_text(encoding="utf-8")
    javascript = UI_JS.read_text(encoding="utf-8")

    assert 'id="navApplyRestore"' in html
    assert "Възстанови конфигурацията" in html
    assert "hidden" in html
    assert "let pendingConfigurationRestore = null;" in javascript
    assert "if (result.changes_detected)" in javascript
    assert "el.navApplyRestore.hidden = false" in javascript


def test_guarded_restore_ui_requires_exact_confirmation():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "window.prompt(" in javascript
    assert 'confirmation !== "RESTORE"' in javascript
    assert "Възстановяването не е потвърдено." in javascript


def test_guarded_restore_ui_sends_validated_snapshot_and_revision():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert 'apiRequest("/restore"' in javascript
    assert "pendingConfigurationRestore.snapshot" in javascript
    assert "expected_current_revision:" in javascript
    assert "pendingConfigurationRestore.expectedCurrentRevision" in javascript
    assert "confirmation," in javascript


def test_guarded_restore_ui_reports_backup_and_reloads_configuration():
    javascript = UI_JS.read_text(encoding="utf-8")

    assert "result.restored_revision" in javascript
    assert "result.backup_identifier" in javascript
    assert "await loadConfiguration()" in javascript
    assert "Грешка при възстановяване:" in javascript
