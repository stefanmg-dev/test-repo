from fastapi.testclient import TestClient

from api import app


client = TestClient(app)


def test_root_redirects_to_configuration_ui():
    response = client.get(
        "/",
        follow_redirects=False
    )

    assert response.status_code in {
        302,
        307,
        308,
    }

    assert response.headers["location"] == (
        "/ui/index.html"
    )


def test_configuration_page_is_available():
    response = client.get(
        "/ui/index.html"
    )

    assert response.status_code == 200
    assert "text/html" in response.headers[
        "content-type"
    ]

    content = response.text

    assert content.startswith(
        "<!DOCTYPE html>"
    )

    assert "Типове документи" in content
    assert "/ui/styles.css" in content
    assert "/ui/ui.js" in content


def test_document_testing_page_is_available():
    response = client.get(
        "/ui/test.html"
    )

    assert response.status_code == 200
    assert "text/html" in response.headers[
        "content-type"
    ]

    content = response.text

    assert content.startswith(
        "<!DOCTYPE html>"
    )

    assert "Тест на документ" in content
    assert "/ui/styles.css" in content
    assert "/ui/test.js" in content


def test_configuration_javascript_is_available():
    response = client.get(
        "/ui/ui.js"
    )

    assert response.status_code == 200

    content = response.text

    assert len(content) > 1000

    assert (
        'const API_BASE = "/api/v1/config"'
        in content
    )

    assert (
        "initializeApplication();"
        in content
    )

    assert (
        "buildValidationPayload"
        in content
    )


def test_document_testing_javascript_is_available():
    response = client.get(
        "/ui/test.js"
    )

    assert response.status_code == 200

    content = response.text

    assert len(content) > 1000

    assert (
        'const CONFIG_URL = '
        '"/api/v1/config/document-types"'
        in content
    )

    assert (
        'const EXTRACT_URL = '
        '"/extract-document"'
        in content
    )

    assert (
        "initializeApplication();"
        in content
    )


def test_stylesheet_is_available():
    response = client.get(
        "/ui/styles.css"
    )

    assert response.status_code == 200
    assert "text/css" in response.headers[
        "content-type"
    ]

    content = response.text

    assert len(content) > 1000
    assert ".app-shell" in content
    assert ".sidebar" in content
    assert ".hidden" in content


def test_ui_files_are_not_html_encoded():
    configuration_page = client.get(
        "/ui/index.html"
    ).text

    testing_page = client.get(
        "/ui/test.html"
    ).text

    assert "&lt;!DOCTYPE html&gt;" not in (
        configuration_page
    )

    assert "&lt;!DOCTYPE html&gt;" not in (
        testing_page
    )


def test_javascript_files_are_not_truncated():
    configuration_javascript = client.get(
        "/ui/ui.js"
    ).text.rstrip()

    testing_javascript = client.get(
        "/ui/test.js"
    ).text.rstrip()

    assert configuration_javascript.endswith(
        "initializeApplication();"
    )

    assert testing_javascript.endswith(
        "initializeApplication();"
    )

def test_authentication_bundle_is_loaded_before_page_scripts():
    for page, script in (
        ("index.html", "/ui/ui.js"),
        ("test.html", "/ui/test.js"),
        ("history.html", "/ui/history.js"),
    ):
        content = client.get(f"/ui/{page}").text
        assert "/ui/auth.bundle.js" in content
        assert content.index("/ui/auth.bundle.js") < content.index(script)


def test_authentication_bundle_is_available():
    response = client.get("/ui/auth.bundle.js")
    assert response.status_code == 200
    assert len(response.text) > 1000
    assert "documentAuth" in response.text
