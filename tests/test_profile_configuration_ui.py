import json
import socket
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent
UI_JS = PROJECT_ROOT / "ui" / "ui.js"
INDEX_HTML = PROJECT_ROOT / "ui" / "index.html"


def read_text(path: Path) -> str:
    return path.read_text(
        encoding="utf-8"
    )


def test_configuration_ui_tracks_resolved_document_types():
    content = read_text(UI_JS)

    assert "resolvedDocumentTypes: {}" in content

    assert (
        "response.resolved_document_types || {}"
        in content
    )


def test_configuration_ui_tracks_selected_field_scope():
    content = read_text(UI_JS)

    assert "selectedFieldScope" in content
    assert "common" in content
    assert "profile" in content


def test_configuration_ui_reads_common_fields():
    content = read_text(UI_JS)

    assert "config.common_fields || []" in content


def test_configuration_ui_reads_profile_fields():
    content = read_text(UI_JS)

    assert "config.profiles" in content
    assert "getSelectedProfile(config)" in content


def test_configuration_ui_uses_common_field_endpoint():
    content = read_text(UI_JS)

    assert "/common-fields" in content


def test_configuration_ui_uses_profile_field_endpoint():
    content = read_text(UI_JS)

    assert "/profiles/" in content


def test_configuration_page_contains_field_scope_control():
    content = read_text(INDEX_HTML)

    assert 'id="fieldScope"' in content


def test_configuration_page_contains_profile_information():
    content = read_text(INDEX_HTML)

    assert 'id="defaultProfileName"' in content
    assert 'id="profileSelector"' in content
    assert 'id="fieldScopeSection"' in content


def test_configuration_ui_tracks_profile_selected_for_editing():
    content = read_text(UI_JS)

    assert "selectedProfileName: null" in content
    assert "state.selectedProfileName = el.profileSelector.value" in content


def test_configuration_ui_profile_selector_does_not_change_default_profile():
    content = read_text(UI_JS)

    listener = content.split(
        'el.profileSelector.addEventListener("change"',
        1,
    )[1].split(
        'el.fieldScope.addEventListener("change"',
        1,
    )[0]
    assert "config.default_profile =" not in listener
    assert 'state.selectedFieldScope = "profile"' in listener


def test_configuration_ui_uses_selected_profile_for_field_endpoint():
    content = read_text(UI_JS)

    assert "const selectedProfile = getSelectedProfile(config);" in content
    assert "encodeURIComponent(selectedProfile)" in content


def available_port():
    with socket.socket() as server_socket:
        server_socket.bind(("127.0.0.1", 0))
        return server_socket.getsockname()[1]


def wait_for_server(port, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(
                ("127.0.0.1", port),
                timeout=0.25,
            ):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError("Uvicorn did not start in time")


@pytest.fixture(scope="module")
def live_server_url():
    port = available_port()
    process = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "api:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        wait_for_server(port)
        yield f"http://127.0.0.1:{port}"
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_configuration_browser_switches_profile_for_editing(
    live_server_url,
):
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [
                    {
                        "name": "invoice_number",
                        "type": "regex",
                        "rule": "Invoice ([0-9]+)",
                    }
                ],
                "profiles": {
                    "telecom_a1": {
                        "fields": [
                            {
                                "name": "contract_number",
                                "type": "regex",
                                "rule": "Contract ([0-9]+)",
                            }
                        ]
                    },
                    "electricity_electrohold": {
                        "fields": [
                            {
                                "name": "supplier_id",
                                "type": "regex",
                                "rule": "ID ([0-9]+)",
                            }
                        ]
                    },
                },
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 9,
            }
        },
    }
    update_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900}
        )
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text)
                if message.type == "error"
                else None
            ),
        )

        page.route(
            "**/api/v1/auth/config",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"enabled": False}),
            ),
        )

        def handle_config(route):
            if route.request.method == "GET":
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(config_body),
                )
                return
            update_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": json.loads(route.request.post_data),
                }
            )
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(config_body),
            )

        page.route(
            "**/api/v1/config/document-types",
            handle_config,
        )
        page.route(
            "**/api/v1/config/document-types/**",
            handle_config,
        )
        page.goto(
            f"{live_server_url}/ui/index.html",
            wait_until="networkidle",
        )

        expect(page.locator("#defaultProfileName")).to_have_text(
            "telecom_a1"
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "telecom_a1"
        )

        page.locator("#fieldScope").select_option("profile")
        expect(page.locator("#fieldList")).to_contain_text(
            "contract_number"
        )
        expect(page.locator("#fieldList")).not_to_contain_text(
            "supplier_id"
        )

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#defaultProfileName")).to_have_text(
            "telecom_a1"
        )
        expect(page.locator("#fieldList")).to_contain_text(
            "supplier_id"
        )
        expect(page.locator("#fieldList")).not_to_contain_text(
            "contract_number"
        )

        page.get_by_role("button", name="Редактирай").click()
        page.locator("#fieldPrimaryValue").fill(
            "Supplier ID ([0-9]+)"
        )
        page.get_by_role("button", name="Запази").click()
        expect(page.get_by_role("dialog")).to_be_hidden()

        browser.close()

    assert len(update_requests) == 1
    assert update_requests[0]["method"] == "PUT"
    assert update_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/fields/supplier_id"
    )
    assert update_requests[0]["body"]["field"]["rule"] == (
        "Supplier ID ([0-9]+)"
    )
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []
