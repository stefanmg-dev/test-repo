import json
import socket
import subprocess
import time
from pathlib import Path

import pytest
from playwright.sync_api import expect, sync_playwright


PROJECT_ROOT = Path(__file__).resolve().parent.parent


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


def test_extraction_browser_renders_evidence_and_validation_scopes(
    live_server_url,
):
    console_errors = []
    extraction_requests = []

    config_body = {
        "document_types": {
            "invoice": {
                "default_profile": "electricity_electrohold",
                "common_fields": [],
                "profiles": {
                    "electricity_electrohold": {
                        "fields": [],
                    }
                },
            }
        },
        "resolved_document_types": {
            "invoice": {
                "fields": [
                    {
                        "name": "invoice_number",
                        "type": "regex",
                        "label": {"bg": "Номер на фактура"},
                    }
                ]
            }
        },
        "document_type_metadata": {
            "invoice": {
                "status": "ready",
                "ready": True,
                "field_count": 1,
            }
        },
    }
    extraction_body = {
        "document_type": "invoice",
        "processing_status": "invalid",
        "profile": "electricity_electrohold",
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "warnings": [],
            "input": {},
        },
        "raw_text": "Synthetic invoice text",
        "llm_values": {"invoice_number": "LLM-123"},
        "final_values": {"invoice_number": "FINAL-123"},
        "field_evidence": {
            "invoice_number": {
                "method": "regex",
                "matched": True,
                "normalized": False,
                "occurrence": "first",
            }
        },
        "collections": {
            "services": [{"amount": "10.00"}],
        },
        "collection_evidence": {
            "services": [
                {
                    "amount": {
                        "method": "regex",
                        "matched": True,
                        "normalized": False,
                        "occurrence": "first",
                    }
                }
            ],
        },
        "collection_validation": {
            "valid": False,
            "errors": {
                "services[0].amount": ["Amount requires review"],
                "_summary.total_amount": ["Summary mismatch"],
            },
        },
        "summary_validation": {
            "valid": False,
            "errors": {
                "_summary.total_amount": ["Summary mismatch"],
            },
        },
        "validation": {
            "valid": False,
            "errors": {
                "invoice_number": ["Invoice number is invalid"],
            },
        },
    }

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1200})
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
        page.route(
            "**/health",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"status": "ok"}),
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

        def handle_extraction(route):
            extraction_requests.append(route.request.method)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(extraction_body),
            )

        page.route("**/extract-document", handle_extraction)
        page.goto(
            f"{live_server_url}/ui/test.html",
            wait_until="networkidle",
        )

        expect(page.locator("#documentType")).to_have_value("invoice")
        page.locator("#documentFile").set_input_files(
            {
                "name": "synthetic.pdf",
                "mimeType": "application/pdf",
                "buffer": b"synthetic-pdf",
            }
        )
        page.locator("#extractButton").click()

        expect(page.locator("#resultSection")).to_be_visible()
        expect(page.locator("#processingStatusBadge")).to_have_text(
            "INVALID"
        )
        expect(page.locator("#validationBadge")).to_have_text(
            "VALIDATION INVALID"
        )
        expect(page.locator("#resultFields")).to_contain_text(
            "FINAL-123"
        )
        expect(page.locator("#resultFields")).to_contain_text(
            "LLM-123"
        )
        expect(page.locator("#resultFields")).to_contain_text("regex")
        expect(page.locator("#resultCollections")).to_contain_text(
            "Extraction method"
        )
        expect(page.locator("#resultCollections")).to_contain_text(
            "Amount requires review"
        )
        expect(page.locator("#summaryValidationBadge")).to_have_text(
            "SUMMARY INVALID"
        )
        expect(page.locator("#summaryValidationErrors")).to_contain_text(
            "total_amount: Summary mismatch"
        )
        expect(page.locator("#diagnosticProfile")).to_have_text(
            "electricity_electrohold"
        )

        assert extraction_requests == ["POST"]
        assert console_errors == []
        browser.close()
