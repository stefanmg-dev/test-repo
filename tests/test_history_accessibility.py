from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_HTML = PROJECT_ROOT / "ui" / "history.html"
HISTORY_JS = PROJECT_ROOT / "ui" / "history.js"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_history_messages_have_status_and_error_semantics():
    html = read(HISTORY_HTML)
    javascript = read(HISTORY_JS)

    assert 'id="historyMessageArea"' in html
    assert 'role="status"' in html
    assert 'aria-live="polite"' in html
    assert 'aria-atomic="true"' in html
    assert 'type === "error" ? "alert" : "status"' in javascript
    assert 'type === "error" ? "assertive" : "polite"' in javascript


def test_history_dialog_preserves_and_restores_trigger_focus():
    content = read(HISTORY_JS)

    assert "dialogReturnFocus: null" in content
    assert "function openHistoryDialog()" in content
    assert "state.dialogReturnFocus =" in content
    assert "elements.closeDialog.focus()" in content
    assert "function restoreHistoryDialogFocus()" in content
    assert "returnFocus?.isConnected" in content
    assert "elements.dialog.addEventListener(" in content
    assert '"close"' in content


def test_history_detail_modes_use_shared_accessible_open_path():
    content = read(HISTORY_JS)

    assert content.count("openHistoryDialog();") == 2
    assert content.count("elements.dialog.showModal();") == 1
