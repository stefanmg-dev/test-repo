from pathlib import Path

from fastapi.testclient import TestClient

from api import app


ROOT = Path(__file__).resolve().parent.parent
HISTORY_HTML = ROOT / "ui" / "history.html"
HISTORY_JS = ROOT / "ui" / "history.js"


def test_processing_history_page_is_available():
    response = TestClient(app).get("/ui/history.html")
    assert response.status_code == 200
    assert "История на обработките" in response.text
    assert "/ui/history.js" in response.text


def test_processing_history_page_has_accessible_controls():
    content = HISTORY_HTML.read_text(encoding="utf-8")
    assert '<table class="history-table">' in content
    assert 'scope="col"' in content
    assert 'role="status"' in content
    assert '<dialog id="historyDetailDialog"' in content
    assert 'label for="filterDocumentType"' in content
    assert 'label for="filterStatus"' in content
    assert 'label for="filterProfile"' in content
    assert 'label for="filterReview"' in content


def test_processing_history_javascript_uses_safe_rendering():
    content = HISTORY_JS.read_text(encoding="utf-8")
    assert 'const HISTORY_URL = "/api/v1/processing-runs"' in content
    assert "document.createElement" in content
    assert ".textContent" in content
    assert "replaceChildren" in content
    assert "innerHTML" not in content
    assert "insertAdjacentHTML" not in content


def test_configuration_page_links_to_history():
    content = (ROOT / "ui" / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'href="/ui/history.html"' in content
