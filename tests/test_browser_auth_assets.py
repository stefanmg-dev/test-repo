from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_browser_api_calls_use_authenticated_fetch():
    for filename in ("ui.js", "test.js", "history.js"):
        content = (ROOT / "ui" / filename).read_text(encoding="utf-8")
        assert "window.documentAuth" in content
    assert "authenticatedFetch" in (ROOT / "ui" / "ui.js").read_text(encoding="utf-8")
    assert "authenticatedFetch" in (ROOT / "ui" / "test.js").read_text(encoding="utf-8")
    assert "authenticatedFetch" in (ROOT / "ui" / "history.js").read_text(encoding="utf-8")


def test_auth_source_uses_msal_without_persisting_tokens():
    content = (ROOT / "ui" / "auth.js").read_text(encoding="utf-8")
    assert '@azure/msal-browser' in content
    assert 'acquireTokenSilent' in content
    assert 'acquireTokenRedirect' in content
    assert 'sessionStorage' in content
    assert 'localStorage' not in content
