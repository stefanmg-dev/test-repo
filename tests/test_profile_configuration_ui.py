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


def test_configuration_modal_keyboard_focus_behavior(
    live_server_url,
):
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                    }
                },
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 900}
        )
        page.route(
            "**/api/v1/auth/config",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"enabled": False}),
            ),
        )
        page.route(
            "**/api/v1/config/document-types",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(config_body),
            ),
        )
        page.goto(
            f"{live_server_url}/ui/index.html",
            wait_until="networkidle",
        )

        trigger = page.locator("#openAddFieldButton")
        trigger.focus()
        expect(trigger).to_be_focused()
        trigger.press("Enter")

        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(page.locator("#fieldName")).to_be_focused()

        page.locator("#confirmModalButton").focus()
        expect(page.locator("#confirmModalButton")).to_be_focused()
        page.keyboard.press("Tab")
        expect(page.locator("#closeModalButton")).to_be_focused()

        page.keyboard.press("Shift+Tab")
        expect(page.locator("#confirmModalButton")).to_be_focused()

        page.keyboard.press("Escape")
        expect(dialog).to_be_hidden()
        expect(trigger).to_be_focused()

        browser.close()


def test_configuration_browser_adds_profile_collection(
    live_server_url,
):
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1000}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            collection_name = route.request.url.rsplit("/", 1)[-1]
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"][collection_name] = request_body[
                "collection"
            ]
            route.fulfill(
                status=201,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection added",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        expect(page.locator("#collectionList")).to_contain_text(
            "Този тип документ още няма колекции."
        )

        page.locator("#openAddCollectionButton").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#collectionName")).to_be_focused()
        page.locator("#collectionName").fill("services")
        page.locator("#collectionCardinality").select_option(
            "one_or_more"
        )
        page.locator("#collectionStartPattern").fill(
            "Service start"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(page.locator("#collectionList")).to_contain_text(
            "services"
        )
        expect(page.locator("#collectionList")).to_contain_text(
            "one_or_more"
        )
        expect(page.locator("#collectionList")).to_contain_text(
            "Service start"
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Колекцията 'services' е добавена."
        )

        browser.close()

    assert len(mutation_requests) == 1
    assert mutation_requests[0]["method"] == "POST"
    assert mutation_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/services"
    )
    assert mutation_requests[0]["body"] == {
        "collection": {
            "cardinality": "one_or_more",
            "fields": [],
            "item_validations": [],
            "start_pattern": "Service start",
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_adds_profile_collection_field(
    live_server_url,
):
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "services": {
                                "cardinality": "one_or_more",
                                "fields": [],
                                "item_validations": [],
                                "start_pattern": "Service start",
                            }
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1100}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["services"]["fields"].append(
                request_body["field"]
            )
            route.fulfill(
                status=201,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection field added",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        expect(page.locator("#collectionList")).to_contain_text(
            "services"
        )
        expect(page.locator("#collectionList")).to_contain_text(
            "Колекцията още няма полета."
        )

        page.get_by_role(
            "button",
            name="Добави поле в колекцията",
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#fieldName")).to_be_focused()
        page.locator("#fieldName").fill("amount")
        page.locator("#fieldType").select_option("regex")
        page.locator("#fieldLabelBg").fill("Сума")
        page.locator("#fieldLabelEn").fill("Amount")
        page.locator("#fieldOccurrence").select_option("first")
        page.locator("#fieldPrimaryValue").fill(
            r"Amount: ([0-9.,]+)"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(page.locator("#collectionList")).to_contain_text(
            "amount · regex"
        )
        expect(page.locator("#collectionList")).not_to_contain_text(
            "Колекцията още няма полета."
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Полето 'amount' е добавено."
        )

        browser.close()

    assert len(mutation_requests) == 1
    assert mutation_requests[0]["method"] == "POST"
    assert mutation_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/services/fields"
    )
    assert mutation_requests[0]["body"] == {
        "field": {
            "name": "amount",
            "type": "regex",
            "label": {
                "bg": "Сума",
                "en": "Amount",
            },
            "rule": r"Amount: ([0-9.,]+)",
            "occurrence": "first",
            "validation": [],
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_adds_item_validation(
    live_server_url,
):
    collection = {
        "cardinality": "one_or_more",
        "fields": [
            {
                "name": "previous_reading",
                "type": "regex",
                "rule": "Previous: ([0-9.]+)",
                "occurrence": "first",
                "validation": [],
            },
            {
                "name": "current_reading",
                "type": "regex",
                "rule": "Current: ([0-9.]+)",
                "occurrence": "first",
                "validation": [],
            },
            {
                "name": "difference",
                "type": "regex",
                "rule": "Difference: ([0-9.]+)",
                "occurrence": "first",
                "validation": [],
            },
        ],
        "item_validations": [],
        "start_pattern": "Reading start",
    }
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "readings": collection,
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1200}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["readings"] = request_body["collection"]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection updated",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        expect(page.locator("#collectionList")).to_contain_text(
            "readings"
        )
        expect(page.locator("#collectionList")).to_contain_text(
            "Колекцията още няма item validations."
        )

        page.get_by_role(
            "button",
            name="Добави item validation",
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#itemValidationType")).to_have_value(
            "difference_equals"
        )
        page.locator("#itemValidationMinuend").select_option(
            "current_reading"
        )
        page.locator("#itemValidationSubtrahend").select_option(
            "previous_reading"
        )
        page.locator("#itemValidationResult").select_option(
            "difference"
        )
        page.locator("#itemValidationMessage").fill(
            "Difference must match readings"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(page.locator("#collectionList")).to_contain_text(
            "difference = current_reading - previous_reading"
        )
        expect(page.locator("#collectionList")).not_to_contain_text(
            "Колекцията още няма item validations."
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Item validation е добавена."
        )

        browser.close()

    assert len(mutation_requests) == 1
    assert mutation_requests[0]["method"] == "PUT"
    assert mutation_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/readings"
    )
    assert mutation_requests[0]["body"] == {
        "collection": {
            **collection,
            "item_validations": [
                {
                    "type": "difference_equals",
                    "minuend": "current_reading",
                    "subtrahend": "previous_reading",
                    "result": "difference",
                    "message": "Difference must match readings",
                }
            ],
        }
    }
    assert mutation_requests[0]["body"]["collection"]["fields"] == (
        collection["fields"]
    )
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_adds_summary_validation(
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
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [
                            {
                                "name": "total_amount",
                                "type": "regex",
                                "rule": "Total: ([0-9.,]+)",
                            }
                        ],
                        "collections": {
                            "services": {
                                "cardinality": "one_or_more",
                                "fields": [
                                    {
                                        "name": "amount",
                                        "type": "regex",
                                        "rule": "Amount: ([0-9.,]+)",
                                        "validation": [],
                                    }
                                ],
                                "item_validations": [],
                            }
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 2,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1200}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["summary_validations"].append(
                request_body["validation"]
            )
            route.fulfill(
                status=201,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Summary validation added",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        expect(page.locator("#summaryValidationSection")).to_be_visible()
        expect(page.locator("#summaryValidationList")).to_contain_text(
            "Профилът още няма summary validations."
        )

        page.locator("#openAddSummaryValidationButton").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#summaryValidationType")).to_have_value(
            "collection_sum_equals_field"
        )
        expect(page.locator("#summaryValidationCollection")).to_have_value(
            "services"
        )
        expect(page.locator("#summaryValidationItemField")).to_have_value(
            "amount"
        )
        page.locator("#summaryValidationTargetField").select_option(
            "total_amount"
        )
        page.locator("#summaryValidationMessage").fill(
            "Service amounts must equal total amount"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(page.locator("#summaryValidationList")).to_contain_text(
            "services.amount = total_amount"
        )
        expect(page.locator("#summaryValidationList")).to_contain_text(
            "collection_sum_equals_field"
        )
        expect(page.locator("#summaryValidationList")).to_contain_text(
            "Service amounts must equal total amount"
        )
        expect(page.locator("#summaryValidationList")).not_to_contain_text(
            "Профилът още няма summary validations."
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Summary validation е добавена."
        )

        browser.close()

    assert len(mutation_requests) == 1
    assert mutation_requests[0]["method"] == "POST"
    assert mutation_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/summary-validations"
    )
    assert mutation_requests[0]["body"] == {
        "validation": {
            "type": "collection_sum_equals_field",
            "collection": "services",
            "item_field": "amount",
            "target_field": "total_amount",
            "message": "Service amounts must equal total amount",
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert config_body["document_types"]["invoice"]["profiles"][
        "telecom_a1"
    ]["summary_validations"] == []
    assert console_errors == []


def test_configuration_browser_edits_profile_collection(
    live_server_url,
):
    collection = {
        "cardinality": "one_or_more",
        "fields": [
            {
                "name": "amount",
                "type": "regex",
                "rule": "Amount: ([0-9.,]+)",
                "occurrence": "first",
                "validation": [],
            },
            {
                "name": "tax",
                "type": "regex",
                "rule": "Tax: ([0-9.,]+)",
                "occurrence": "first",
                "validation": [],
            },
            {
                "name": "total",
                "type": "regex",
                "rule": "Total: ([0-9.,]+)",
                "occurrence": "first",
                "validation": [],
            },
        ],
        "item_validations": [
            {
                "type": "difference_equals",
                "minuend": "total",
                "subtrahend": "tax",
                "result": "amount",
                "message": "Amount must equal total minus tax",
            }
        ],
        "start_pattern": "Service start",
    }
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "services": collection,
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1200}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["services"] = request_body["collection"]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection updated",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        collection_card = page.locator("#collectionList .field-card").filter(
            has_text="services"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("one_or_more")
        expect(collection_card).to_contain_text("Service start")
        expect(collection_card).to_contain_text("fields")
        expect(collection_card).to_contain_text("3")
        expect(collection_card).to_contain_text("item_validations")
        expect(collection_card).to_contain_text("1")

        collection_card.get_by_role(
            "button",
            name="Редактирай",
            exact=True,
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#collectionName")).to_be_disabled()
        expect(page.locator("#collectionName")).to_have_value("services")
        page.locator("#collectionCardinality").select_option(
            "exactly_one"
        )
        page.locator("#collectionStartPattern").fill(
            "Updated service start"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator("#collectionList .field-card").filter(
            has_text="services"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("exactly_one")
        expect(collection_card).to_contain_text("Updated service start")
        expect(collection_card).not_to_contain_text("Service start")
        expect(collection_card).to_contain_text("amount · regex")
        expect(collection_card).to_contain_text("tax · regex")
        expect(collection_card).to_contain_text("total · regex")
        expect(collection_card).to_contain_text(
            "amount = total - tax"
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Колекцията 'services' е актуализирана."
        )

        browser.close()

    assert len(mutation_requests) == 1
    assert mutation_requests[0]["method"] == "PUT"
    assert mutation_requests[0]["url"].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/services"
    )
    assert mutation_requests[0]["body"] == {
        "collection": {
            "cardinality": "exactly_one",
            "fields": collection["fields"],
            "item_validations": collection["item_validations"],
            "start_pattern": "Updated service start",
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_deletes_profile_collection(
    live_server_url,
):
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "services": {
                                "cardinality": "one_or_more",
                                "fields": [],
                                "item_validations": [],
                                "start_pattern": "Service start",
                            }
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    delete_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1000}
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

            assert route.request.method == "DELETE"
            delete_requests.append(route.request.url)
            del config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["services"]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection deleted",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="services")
        expect(collection_card).to_have_count(1)

        collection_card.get_by_role(
            "button",
            name="Изтрий",
            exact=True,
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#modalTitle")).to_have_text(
            "Изтриване на колекция"
        )
        expect(page.locator("#modalBody")).to_contain_text(
            "Изтриване на колекцията 'services'"
        )
        page.locator("#cancelModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(collection_card).to_have_count(1)
        assert delete_requests == []

        collection_card.get_by_role(
            "button",
            name="Изтрий",
            exact=True,
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#confirmModalButton")).to_have_text(
            "Изтрий"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(page.locator("#collectionList .field-card")).to_have_count(0)
        expect(page.locator("#collectionList")).to_contain_text(
            "Този тип документ още няма колекции."
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#fieldScope")).to_have_value("profile")
        expect(page.locator("#messageArea")).to_contain_text(
            "Колекцията 'services' е изтрита."
        )

        browser.close()

    assert len(delete_requests) == 1
    assert delete_requests[0].endswith(
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/services"
    )
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_retries_failed_collection_edit(
    live_server_url,
):
    original_collection = {
        "cardinality": "one_or_more",
        "fields": [
            {
                "name": "amount",
                "type": "regex",
                "rule": "Amount: ([0-9.,]+)",
                "occurrence": "first",
                "validation": [],
            }
        ],
        "item_validations": [],
        "start_pattern": "Original service start",
    }
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "services": original_collection,
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1100}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            if len(mutation_requests) == 1:
                route.fulfill(
                    status=409,
                    content_type="application/json",
                    body=json.dumps(
                        {
                            "detail": (
                                "Configuration changed; retry save"
                            )
                        }
                    ),
                )
                return

            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["services"] = request_body["collection"]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(
                    {
                        "status": "ok",
                        "message": "Collection updated",
                    }
                ),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="services")
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("one_or_more")
        expect(collection_card).to_contain_text(
            "Original service start"
        )

        collection_card.get_by_role(
            "button",
            name="Редактирай",
            exact=True,
        ).click()
        page.locator("#collectionCardinality").select_option(
            "exactly_one"
        )
        page.locator("#collectionStartPattern").fill(
            "Retried service start"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#collectionCardinality")).to_have_value(
            "exactly_one"
        )
        expect(page.locator("#collectionStartPattern")).to_have_value(
            "Retried service start"
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Configuration changed; retry save"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("one_or_more")
        expect(collection_card).to_contain_text(
            "Original service start"
        )
        expect(collection_card).not_to_contain_text(
            "Retried service start"
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#fieldScope")).to_have_value("profile")

        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="services")
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("exactly_one")
        expect(collection_card).to_contain_text(
            "Retried service start"
        )
        expect(collection_card).not_to_contain_text(
            "Original service start"
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Колекцията 'services' е актуализирана."
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#fieldScope")).to_have_value("profile")

        browser.close()

    assert len(mutation_requests) == 2
    assert [request["method"] for request in mutation_requests] == [
        "PUT",
        "PUT",
    ]
    assert all(
        request["url"].endswith(
            "/api/v1/config/document-types/invoice/profiles/"
            "electricity_electrohold/collections/services"
        )
        for request in mutation_requests
    )
    assert mutation_requests[0]["body"] == mutation_requests[1]["body"]
    assert mutation_requests[1]["body"] == {
        "collection": {
            "cardinality": "exactly_one",
            "fields": original_collection["fields"],
            "item_validations": original_collection[
                "item_validations"
            ],
            "start_pattern": "Retried service start",
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert len(console_errors) == 1
    assert "409 (Conflict)" in console_errors[0]


def test_configuration_browser_edits_and_deletes_profile_collection_field(
    live_server_url,
):
    amount_field = {
        "name": "amount",
        "type": "regex",
        "label": {"bg": "Сума", "en": "Amount"},
        "rule": "Amount: ([0-9.,]+)",
        "occurrence": "first",
        "validation": [],
    }
    tax_field = {
        "name": "tax",
        "type": "regex",
        "label": {"bg": "Данък", "en": "Tax"},
        "rule": "Tax: ([0-9.,]+)",
        "occurrence": "first",
        "validation": [],
    }
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "services": {
                                "cardinality": "one_or_more",
                                "fields": [amount_field, tax_field],
                                "item_validations": [],
                            }
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1280, "height": 1200})
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

            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": (
                        json.loads(route.request.post_data)
                        if route.request.post_data
                        else None
                    ),
                }
            )
            fields = config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["services"]["fields"]
            if route.request.method == "PUT":
                updated_field = mutation_requests[-1]["body"]["field"]
                fields[0] = updated_field
                status = 200
            else:
                assert route.request.method == "DELETE"
                fields[:] = [field for field in fields if field["name"] != "amount"]
                status = 204
            route.fulfill(
                status=status,
                content_type="application/json",
                body=(
                    json.dumps({"status": "ok"})
                    if status != 204
                    else ""
                ),
            )

        page.route("**/api/v1/config/document-types", handle_config)
        page.route("**/api/v1/config/document-types/**", handle_config)
        page.goto(
            f"{live_server_url}/ui/index.html",
            wait_until="networkidle",
        )

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        collection_card = page.locator("#collectionList .field-card").filter(
            has_text="services"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card).to_contain_text("amount · regex")
        expect(collection_card).to_contain_text("tax · regex")

        amount_row = collection_card.locator(".field-detail").filter(
            has_text="amount · regex"
        )
        amount_row.get_by_role("button", name="Редактирай поле").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        page.locator("#fieldPrimaryValue").fill(
            "Updated amount: ([0-9.,]+)"
        )
        page.locator("#fieldOccurrence").select_option("last")
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator("#collectionList .field-card").filter(
            has_text="services"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card.locator(".field-detail").filter(
            has_text="amount · regex"
        )).to_have_count(1)
        expect(collection_card).to_contain_text("tax · regex")
        expect(page.locator("#messageArea")).to_contain_text(
            "Полето 'amount' е актуализирано."
        )

        amount_row = collection_card.locator(".field-detail").filter(
            has_text="amount · regex"
        )
        amount_row.get_by_role("button", name="Изтрий поле").click()
        expect(page.get_by_role("dialog")).to_be_visible()
        page.locator("#cancelModalButton").click()
        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(collection_card).to_contain_text("amount · regex")
        assert len(mutation_requests) == 1

        amount_row.get_by_role("button", name="Изтрий поле").click()
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator("#collectionList .field-card").filter(
            has_text="services"
        )
        expect(collection_card).to_have_count(1)
        expect(collection_card).not_to_contain_text("amount · regex")
        expect(collection_card).to_contain_text("tax · regex")
        expect(collection_card.locator(".field-detail").filter(
            has_text="tax · regex"
        )).to_have_count(1)
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#fieldScope")).to_have_value("profile")
        expect(page.locator("#messageArea")).to_contain_text(
            "Полето 'amount' е изтрито."
        )

        browser.close()

    assert [request["method"] for request in mutation_requests] == [
        "PUT",
        "DELETE",
    ]
    expected_endpoint = (
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/services/fields/amount"
    )
    assert all(
        request["url"].endswith(expected_endpoint)
        for request in mutation_requests
    )
    assert mutation_requests[0]["body"] == {
        "field": {
            **amount_field,
            "rule": "Updated amount: ([0-9.,]+)",
            "occurrence": "last",
        }
    }
    assert mutation_requests[1]["body"] is None
    assert config_body["document_types"]["invoice"]["profiles"][
        "electricity_electrohold"
    ]["collections"]["services"]["fields"] == [tax_field]
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []


def test_configuration_browser_edits_and_deletes_item_validation(
    live_server_url,
):
    fields = [
        {
            "name": "previous_reading",
            "type": "regex",
            "rule": "Previous: ([0-9.]+)",
            "validation": [],
        },
        {
            "name": "current_reading",
            "type": "regex",
            "rule": "Current: ([0-9.]+)",
            "validation": [],
        },
        {
            "name": "difference",
            "type": "regex",
            "rule": "Difference: ([0-9.]+)",
            "validation": [],
        },
    ]
    original_validation = {
        "type": "difference_equals",
        "minuend": "current_reading",
        "subtrahend": "previous_reading",
        "result": "difference",
        "message": "Original validation message",
    }
    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "telecom_a1",
                "common_fields": [],
                "profiles": {
                    "telecom_a1": {
                        "fields": [],
                        "collections": {},
                        "summary_validations": [],
                    },
                    "electricity_electrohold": {
                        "fields": [],
                        "collections": {
                            "readings": {
                                "cardinality": "one_or_more",
                                "fields": fields,
                                "item_validations": [
                                    original_validation,
                                ],
                            }
                        },
                        "summary_validations": [],
                    },
                },
                "collections": {},
            }
        },
        "resolved_document_types": {},
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 0,
            }
        },
    }
    mutation_requests = []
    console_errors = []

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 1200}
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

            request_body = json.loads(route.request.post_data)
            mutation_requests.append(
                {
                    "method": route.request.method,
                    "url": route.request.url,
                    "body": request_body,
                }
            )
            config_body["document_types"]["invoice"]["profiles"][
                "electricity_electrohold"
            ]["collections"]["readings"] = request_body[
                "collection"
            ]
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"status": "ok"}),
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

        page.locator("#profileSelector").select_option(
            "electricity_electrohold"
        )
        page.locator("#fieldScope").select_option("profile")
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="readings")
        validation_row = collection_card.locator(
            ".field-detail"
        ).filter(
            has_text=(
                "difference = current_reading"
                " - previous_reading"
            )
        )
        expect(validation_row).to_have_count(1)

        validation_row.get_by_role(
            "button",
            name="Редактирай validation",
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        expect(page.locator("#itemValidationMinuend")).to_have_value(
            "current_reading"
        )
        expect(page.locator("#itemValidationSubtrahend")).to_have_value(
            "previous_reading"
        )
        expect(page.locator("#itemValidationResult")).to_have_value(
            "difference"
        )
        expect(page.locator("#itemValidationMessage")).to_have_value(
            "Original validation message"
        )
        page.locator("#itemValidationMinuend").select_option(
            "difference"
        )
        page.locator("#itemValidationSubtrahend").select_option(
            "previous_reading"
        )
        page.locator("#itemValidationResult").select_option(
            "current_reading"
        )
        page.locator("#itemValidationMessage").fill(
            "Updated validation message"
        )
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="readings")
        updated_row = collection_card.locator(
            ".field-detail"
        ).filter(
            has_text=(
                "current_reading = difference"
                " - previous_reading"
            )
        )
        expect(updated_row).to_have_count(1)
        expect(collection_card).not_to_contain_text(
            "difference = current_reading - previous_reading"
        )
        expect(page.locator("#messageArea")).to_contain_text(
            "Item validation е актуализирана."
        )

        updated_row.get_by_role(
            "button",
            name="Изтрий validation",
        ).click()
        expect(page.get_by_role("dialog")).to_be_visible()
        page.locator("#cancelModalButton").click()
        expect(page.get_by_role("dialog")).to_be_hidden()
        expect(updated_row).to_have_count(1)
        assert len(mutation_requests) == 1

        updated_row.get_by_role(
            "button",
            name="Изтрий validation",
        ).click()
        page.locator("#confirmModalButton").click()

        expect(page.get_by_role("dialog")).to_be_hidden()
        collection_card = page.locator(
            "#collectionList .field-card"
        ).filter(has_text="readings")
        expect(collection_card).not_to_contain_text(
            "current_reading = difference - previous_reading"
        )
        expect(collection_card).to_contain_text(
            "Колекцията още няма item validations."
        )
        expect(page.locator("#profileSelector")).to_have_value(
            "electricity_electrohold"
        )
        expect(page.locator("#fieldScope")).to_have_value("profile")
        expect(page.locator("#messageArea")).to_contain_text(
            "Item validation е изтрита."
        )

        browser.close()

    assert [request["method"] for request in mutation_requests] == [
        "PUT",
        "PUT",
    ]
    expected_endpoint = (
        "/api/v1/config/document-types/invoice/profiles/"
        "electricity_electrohold/collections/readings"
    )
    assert all(
        request["url"].endswith(expected_endpoint)
        for request in mutation_requests
    )
    assert mutation_requests[0]["body"] == {
        "collection": {
            "cardinality": "one_or_more",
            "fields": fields,
            "item_validations": [
                {
                    "type": "difference_equals",
                    "minuend": "difference",
                    "subtrahend": "previous_reading",
                    "result": "current_reading",
                    "message": "Updated validation message",
                }
            ],
        }
    }
    assert mutation_requests[1]["body"] == {
        "collection": {
            "cardinality": "one_or_more",
            "fields": fields,
            "item_validations": [],
        }
    }
    assert config_body["document_types"]["invoice"][
        "default_profile"
    ] == "telecom_a1"
    assert console_errors == []
