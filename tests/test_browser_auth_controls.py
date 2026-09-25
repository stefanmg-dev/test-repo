from pathlib import Path

from fastapi.testclient import TestClient

from api import app


ROOT = Path(__file__).resolve().parents[1]


def test_auth_controls_asset_is_available():
    response = TestClient(app).get("/ui/auth-controls.js")
    assert response.status_code == 200
    assert "initializeAuthControls" in response.text
    assert "signIn" in response.text
    assert "signOut" in response.text


def test_auth_controls_load_after_bundle_and_before_page_scripts():
    for page, page_script in (
        ("index.html", "/ui/ui.js"),
        ("test.html", "/ui/test.js"),
        ("history.html", "/ui/history.js"),
    ):
        content = (ROOT / "ui" / page).read_text(encoding="utf-8")
        assert content.index("/ui/auth.bundle.js") < content.index(
            "/ui/auth-controls.js"
        )
        assert content.index("/ui/auth-controls.js") < content.index(
            page_script
        )


def test_auth_controls_are_hidden_when_oidc_is_disabled():
    content = (ROOT / "ui" / "auth-controls.js").read_text(
        encoding="utf-8"
    )
    assert 'className = "auth-controls hidden"' in content
    assert "isEnabled()" in content
    assert 'classList.remove("hidden")' in content


def test_auth_controls_use_safe_dom_rendering():
    content = (ROOT / "ui" / "auth-controls.js").read_text(
        encoding="utf-8"
    )
    assert "document.createElement" in content
    assert ".textContent" in content
    assert "innerHTML" not in content
    assert "insertAdjacentHTML" not in content
