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
        "final_values": {
            "invoice_number": "TEST-123"
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

        page.get_by_label("Тип документ").fill("invoice")
        page.get_by_label("Статус").select_option("accepted")
        page.get_by_label("Профил").fill("telecom_a1")
        page.get_by_label("Изисква проверка").select_option(
            "false"
        )
        page.get_by_role("button", name="Приложи").click()
        page.wait_for_load_state("networkidle")

        assert any(
            "document_type=invoice" in url
            and "processing_status=accepted" in url
            and "profile=telecom_a1" in url
            and "requires_review=false" in url
            for url in list_requests
        )

        page.get_by_role("button", name="Отвори").click()
        dialog = page.get_by_role("dialog")
        expect(dialog).to_be_visible()
        expect(
            dialog.get_by_text("TEST-123")
        ).to_be_visible()
        expect(
            dialog.get_by_text("document_input_ms")
        ).to_be_visible()
        page.get_by_role("button", name="Затвори").click()
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
