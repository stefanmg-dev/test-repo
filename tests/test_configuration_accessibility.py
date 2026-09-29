from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INDEX_HTML = PROJECT_ROOT / "ui" / "index.html"
UI_JS = PROJECT_ROOT / "ui" / "ui.js"
STYLES = PROJECT_ROOT / "ui" / "styles.css"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_configuration_modal_has_accessible_dialog_contract():
    content = read(INDEX_HTML)

    assert 'id="configurationModal"' in content
    assert 'role="dialog"' in content
    assert 'aria-modal="true"' in content
    assert 'aria-labelledby="modalTitle"' in content
    assert 'tabindex="-1"' in content


def test_configuration_modal_preserves_and_restores_focus():
    content = read(UI_JS)

    assert "modalReturnFocus: null" in content
    assert "state.modalReturnFocus =" in content
    assert "returnFocus?.isConnected" in content
    assert "returnFocus.focus()" in content


def test_configuration_modal_traps_tab_and_supports_escape():
    content = read(UI_JS)

    assert "function trapModalFocus(event)" in content
    assert 'event.key !== "Tab"' in content
    assert "event.shiftKey" in content
    assert 'event.key === "Escape"' in content
    assert "trapModalFocus(event)" in content


def test_configuration_controls_have_visible_keyboard_focus():
    content = read(STYLES)

    for selector in (
        ".button:focus-visible",
        ".icon-button:focus-visible",
        ".nav-item:focus-visible",
        ".document-type-item:focus-visible",
        ".form-control:focus-visible",
    ):
        assert selector in content
    assert "outline:" in content
    assert "outline-offset:" in content
