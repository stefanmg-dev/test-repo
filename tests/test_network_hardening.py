import os
import subprocess
import sys

from fastapi.testclient import TestClient

from api import app
from app_settings import AppSettings


def settings(**overrides):
    values = {
        "DATABASE_URL": "postgresql+psycopg://u:p@localhost/db",
        **overrides,
    }
    return AppSettings(_env_file=None, **values)


def test_default_host_allowlist_supports_local_and_tests():
    configured = settings().allowed_hosts_list()

    assert configured == ["localhost", "127.0.0.1", "testserver"]


def test_rejects_untrusted_host():
    response = TestClient(app).get(
        "/health",
        headers={"Host": "attacker.example"},
    )

    assert response.status_code == 400
    assert response.text == "Invalid host header"


def test_accepts_configured_test_host():
    response = TestClient(app).get(
        "/health",
        headers={"Host": "testserver"},
    )

    assert response.status_code == 200


def test_cors_is_disabled_by_default():
    response = TestClient(app).get(
        "/health",
        headers={"Origin": "https://attacker.example"},
    )

    assert "access-control-allow-origin" not in response.headers


def test_comma_separated_network_settings_are_normalized():
    configured = settings(
        ALLOWED_HOSTS="api.example.com, internal.example.com",
        CORS_ALLOWED_ORIGINS=(
            "https://app.example.com, https://admin.example.com"
        ),
    )

    assert configured.allowed_hosts_list() == [
        "api.example.com",
        "internal.example.com",
    ]
    assert configured.cors_allowed_origins_list() == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_production_disables_public_api_docs():
    environment = {
        **os.environ,
        "ENVIRONMENT": "production",
        "EXPOSE_API_DOCS": "false",
        "ALLOWED_HOSTS": "api.example.com",
    }
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from api import app; "
                "assert app.docs_url is None; "
                "assert app.redoc_url is None; "
                "assert app.openapi_url is None"
            ),
        ],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        env=environment,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
