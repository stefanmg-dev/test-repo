import importlib.util
import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = PROJECT_ROOT / "scripts" / "deployment_smoke.py"


def load_module():
    spec = importlib.util.spec_from_file_location("deployment_smoke", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def healthy_responses(authenticated=False):
    responses = {
        "/health": (200, {"status": "ok"}),
        "/ready": (
            200,
            {
                "status": "ready",
                "database": "connected",
                "migrations": "current",
                "revision": "revision-123",
            },
        ),
        "/api/v1/auth/config": (
            200,
            {"enabled": True, "redirect_path": "/ui/index.html", "scopes": []},
        ),
        "/api/v1/processing-runs?offset=0&limit=1": (
            (200, {"items": [], "total": 0, "offset": 0, "limit": 1})
            if authenticated
            else (401, {"detail": "Authentication required"})
        ),
    }
    return responses


def install_fake_request(monkeypatch, module, responses, calls):
    def fake_request(base_url, path, *, headers=None, timeout=10):
        calls.append((base_url, path, headers or {}, timeout))
        return responses[path]

    monkeypatch.setattr(module, "request", fake_request)


def test_anonymous_smoke_is_read_only_and_requires_401(monkeypatch):
    module = load_module()
    calls = []
    install_fake_request(monkeypatch, module, healthy_responses(), calls)

    result = module.run_smoke("https://production.example.com")

    assert result == 0
    assert [call[1] for call in calls] == [
        "/health",
        "/ready",
        "/api/v1/auth/config",
        "/api/v1/processing-runs?offset=0&limit=1",
    ]
    assert all(call[2] == {} for call in calls)


def test_api_key_smoke_uses_only_api_key_header(monkeypatch):
    module = load_module()
    calls = []
    install_fake_request(monkeypatch, module, healthy_responses(True), calls)

    module.run_smoke(
        "https://production.example.com",
        api_key="secret-api-key",
    )

    assert calls[-1][2] == {"X-API-Key": "secret-api-key"}


def test_bearer_smoke_uses_only_authorization_header(monkeypatch):
    module = load_module()
    calls = []
    install_fake_request(monkeypatch, module, healthy_responses(True), calls)

    module.run_smoke(
        "https://production.example.com",
        bearer_token="secret-token",
    )

    assert calls[-1][2] == {"Authorization": "Bearer secret-token"}


def test_smoke_rejects_http_and_multiple_authentication_mechanisms():
    module = load_module()

    with pytest.raises(RuntimeError, match="must use HTTPS"):
        module.run_smoke("http://production.example.com")

    with pytest.raises(RuntimeError, match="either"):
        module.run_smoke(
            "https://production.example.com",
            api_key="key",
            bearer_token="token",
        )


def test_smoke_rejects_not_ready_response(monkeypatch):
    module = load_module()
    calls = []
    responses = healthy_responses()
    responses["/ready"] = (503, {"status": "not_ready"})
    install_fake_request(monkeypatch, module, responses, calls)

    with pytest.raises(RuntimeError, match="/ready did not return HTTP 200"):
        module.run_smoke("https://production.example.com")


def test_cli_failure_does_not_print_credentials(monkeypatch):
    module = load_module()

    def fail(*args, **kwargs):
        raise RuntimeError("safe failure")

    monkeypatch.setattr(module, "run_smoke", fail)
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        result = module.main(
            [
                "--base-url",
                "https://production.example.com",
                "--api-key",
                "secret-api-key",
            ]
        )

    assert result == 1
    output = stdout.getvalue() + stderr.getvalue()
    assert "safe failure" in output
    assert "secret-api-key" not in output
