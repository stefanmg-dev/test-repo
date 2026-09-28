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


def test_processing_history_browser_smoke(live_server_url):
    run_id = "11111111-1111-1111-1111-111111111111"
    list_requests = []
    console_errors = []
    review_requests = []
    universal_invoice_requests = []

    list_body = {
        "items": [
            {
                "id": run_id,
                "document_type": "invoice",
                "profile": "telecom_a1",
                "filename": "browser-smoke.pdf",
                "input_format": "pdf",
                "processing_status": "accepted",
                "requires_review": False,
                "started_at": "2026-09-22T18:00:00Z",
                "completed_at": "2026-09-22T18:00:01Z",
                "duration_ms": 321,
                "created_at": "2026-09-22T18:00:00Z",
            }
        ],
        "total": 1,
        "offset": 0,
        "limit": 20,
    }
    invoice_shadow_summary_body = {
        "total": 5,
        "succeeded": 3,
        "failed": 1,
        "not_applicable": 1,
        "success_rate": 0.75,
        "schema_versions": [
            {
                "schema_version": "1",
                "total": 4,
                "succeeded": 3,
                "failed": 1,
            }
        ],
        "failure_reasons": [
            {
                "reason": "validation_error",
                "count": 1,
            }
        ],
    }
    review_summary_body = {
        "total_requiring_review": 10,
        "pending": 4,
        "approved": 2,
        "corrected": 3,
        "rejected": 1,
        "average_review_duration_ms": 1500,
    }

    detail_body = {
        **list_body["items"][0],
        "step_timings": {
            "document_input_ms": 120,
            "document_engine_ms": 80,
        },
        "quality": {
            "status": "accepted",
            "requires_review": False,
            "warnings": [],
        },
        "review_status": "pending",
        "invoice_schema_version": "1",
        "invoice_shadow_validation_status": "failed",
        "invoice_shadow_validation_reason": "validation_error",
        "final_values": {
            "invoice_number": "TEST-123",
            "page_count": 1,
        },
        "configuration_snapshot": {
            "resolved_fields": [
                {
                    "name": "invoice_number",
                    "label": {"bg": "Номер на фактура"},
                },
                {
                    "name": "page_count",
                    "label": {"bg": "Брой страници"},
                },
            ],
        },
        "collections": {},
        "validation": {
            "fields": {"valid": True, "errors": {}},
            "collections": {"valid": True, "errors": {}},
        },
        "error": None,
        "updated_at": "2026-09-22T18:00:01Z",
    }

    with sync_playwright() as playwright:
        executable = Path(
            playwright.chromium.executable_path
        )
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1280, "height": 800}
        )
        page.on(
            "console",
            lambda message: (
                console_errors.append(message.text)
                if message.type == "error"
                else None
            ),
        )

        def handle_history(route):
            list_requests.append(route.request.url)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(list_body),
            )

        page.route(
            "**/api/v1/processing-runs?*",
            handle_history,
        )
        page.route(
            "**/api/v1/processing-runs/invoice-shadow-summary",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(invoice_shadow_summary_body),
            ),
        )
        page.route(
            "**/api/v1/processing-runs/review-summary",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(review_summary_body),
            ),
        )
        def handle_review(route):
            review_requests.append(
                json.loads(route.request.post_data)
            )
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "processing_run_id": run_id,
                    "status": "corrected",
                    "original_values": detail_body[
                        "final_values"
                    ],
                    "corrected_values": {
                        "invoice_number": "TEST-456",
                        "page_count": 2,
                    },
                    "effective_values": {
                        "invoice_number": "TEST-456",
                        "page_count": 2,
                    },
                    "comment": "Browser review",
                    "reviewed_at": (
                        "2026-09-22T18:05:00Z"
                    ),
                    "reviewed_by_type": "user",
                    "reviewed_by_subject": "browser-user",
                }),
            )

        page.route(
            f"**/api/v1/processing-runs/{run_id}/review",
            handle_review,
        )

        def handle_universal_invoice(route):
            universal_invoice_requests.append(route.request.url)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "schema_version": "1",
                    "invoice_number": "TEST-123",
                    "services": [],
                    "metering_points": [],
                    "meters": [],
                    "consumption_items": [],
                }),
            )

        page.route(
            f"**/api/v1/processing-runs/{run_id}/universal-invoice",
            handle_universal_invoice,
        )

        page.route(
            f"**/api/v1/processing-runs/{run_id}",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(detail_body),
            ),
        )

        page.goto(
            f"{live_server_url}/ui/history.html",
            wait_until="networkidle",
        )

        assert page.get_by_role(
            "heading",
            name="История на обработките",
        ).is_visible()
        assert page.get_by_text("browser-smoke.pdf").is_visible()
        assert page.get_by_role(
            "cell",
            name="accepted",
        ).is_visible()
        assert page.get_by_text(
            "Намерени обработки: 1"
        ).is_visible()
        assert page.locator("#reviewTotal").inner_text() == "10"
        assert page.locator("#reviewPending").inner_text() == "4"
        assert page.locator("#reviewApproved").inner_text() == "2"
        assert page.locator("#reviewCorrected").inner_text() == "3"
        assert page.locator("#reviewRejected").inner_text() == "1"
        assert page.locator(
            "#reviewAverageDuration"
        ).inner_text() == "1.5 s"
        assert page.locator("#invoiceShadowTotal").inner_text() == "5"
        assert page.locator(
            "#invoiceShadowSucceeded"
        ).inner_text() == "3"
        assert page.locator("#invoiceShadowFailed").inner_text() == "1"
        assert page.locator(
            "#invoiceShadowNotApplicable"
        ).inner_text() == "1"
        assert page.locator(
            "#invoiceShadowSuccessRate"
        ).inner_text() == "75.0%"
        assert page.locator(
            "#invoiceShadowSchemaVersions"
        ).inner_text() == "1: 4"
        assert page.locator(
            "#invoiceShadowFailureReasons"
        ).inner_text() == "validation_error: 1"

        page.get_by_label("Тип документ").fill("invoice")
        page.get_by_label("Статус", exact=True).select_option("accepted")
        page.get_by_label("Профил").fill("telecom_a1")
        page.get_by_label("Изисква проверка").select_option(
            "false"
        )
        page.get_by_label(
            "Invoice shadow статус"
        ).select_option("succeeded")
        page.get_by_label("Invoice schema version").fill("1")
        page.get_by_role("button", name="Приложи").click()
        page.wait_for_load_state("networkidle")

        assert any(
            "document_type=invoice" in url
            and "processing_status=accepted" in url
            and "profile=telecom_a1" in url
            and "requires_review=false" in url
            and "invoice_shadow_validation_status=succeeded" in url
            and "invoice_schema_version=1" in url
            for url in list_requests
        )

        page.get_by_role("button", name="Universal Invoice").click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(
            dialog.get_by_text("Universal Invoice", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("TEST-123", exact=False)
        ).to_be_visible()
        assert len(universal_invoice_requests) == 1
        dialog.get_by_role("button", name="Затвори").click()
        expect(dialog).to_be_hidden()

        page.evaluate("""
            window.documentAuth.isEnabled = () => true;
            window.documentAuth.isAuthenticated = () => true;
        """)

        page.get_by_role("button", name="Отвори").click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(
            dialog.get_by_text("TEST-123", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("document_input_ms")
        ).to_be_visible()
        expect(
            dialog.get_by_text("Invoice schema version", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("Invoice shadow статус", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("failed", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("Invoice shadow причина", exact=True)
        ).to_be_visible()
        expect(
            dialog.get_by_text("validation_error", exact=True)
        ).to_be_visible()
        invoice_input = page.locator(
            "#reviewField-invoice_number"
        )
        page_count_input = page.locator(
            "#reviewField-page_count"
        )

        expect(invoice_input).to_have_value("TEST-123")
        expect(page_count_input).to_have_value("1")

        invoice_input.fill("TEST-456")
        page_count_input.fill("2")
        page.locator("#reviewComment").fill("Browser review")

        changed_row = invoice_input.locator(
            "xpath=ancestor::*[contains("
            "@class, 'review-field-row')]"
        )
        assert "review-field-changed" in (
            changed_row.get_attribute("class") or ""
        )

        page.get_by_role("button", name="Correct").click()

        page.wait_for_timeout(100)

        assert review_requests == [
            {
                "status": "corrected",
                "comment": "Browser review",
                "corrected_values": {
                    "invoice_number": "TEST-456",
                    "page_count": 2,
                },
            }
        ]

        expect(dialog).to_be_hidden()

        assert page.get_by_role(
            "button",
            name="Предишна",
        ).is_disabled()
        assert page.get_by_role(
            "button",
            name="Следваща",
        ).is_disabled()
        assert console_errors == []

        browser.close()

def test_universal_invoice_preview_handles_unavailable(live_server_url):
    run_id = "22222222-2222-2222-2222-222222222222"
    list_body = {
        "items": [
            {
                "id": run_id,
                "document_type": "invoice",
                "profile": None,
                "filename": "unavailable.pdf",
                "input_format": "pdf",
                "processing_status": "accepted",
                "requires_review": False,
                "started_at": "2026-09-22T18:00:00Z",
                "completed_at": "2026-09-22T18:00:01Z",
                "duration_ms": 100,
                "created_at": "2026-09-22T18:00:00Z",
            }
        ],
        "total": 1,
        "offset": 0,
        "limit": 20,
    }

    with sync_playwright() as playwright:
        executable = Path(playwright.chromium.executable_path)
        if not executable.exists():
            pytest.skip("Playwright Chromium is not installed")

        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.route(
            "**/api/v1/processing-runs?*",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(list_body),
            ),
        )
        page.route(
            "**/api/v1/processing-runs/review-summary",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "total_requiring_review": 0,
                    "pending": 0,
                    "approved": 0,
                    "corrected": 0,
                    "rejected": 0,
                    "average_review_duration_ms": None,
                }),
            ),
        )
        page.route(
            "**/api/v1/processing-runs/invoice-shadow-summary",
            lambda route: route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "total": 0,
                    "succeeded": 0,
                    "failed": 0,
                    "not_applicable": 0,
                    "success_rate": None,
                    "schema_versions": [],
                    "failure_reasons": [],
                }),
            ),
        )
        page.route(
            f"**/api/v1/processing-runs/{run_id}/universal-invoice",
            lambda route: route.fulfill(
                status=409,
                content_type="application/json",
                body=json.dumps({
                    "detail": (
                        "Universal invoice mapping is unavailable for this run"
                    )
                }),
            ),
        )

        page.goto(
            f"{live_server_url}/ui/history.html",
            wait_until="networkidle",
        )
        page.get_by_role("button", name="Universal Invoice").click()

        expect(page.locator("#historyMessageArea")).to_contain_text(
            "Universal Invoice не е достъпен"
        )
        expect(page.get_by_role("dialog")).to_be_hidden()
        browser.close()
