from fastapi.testclient import TestClient
from pydantic import ValidationError
import pytest

from api import app
from app_settings import AppSettings, get_settings


def settings(**overrides):
    return AppSettings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
        **overrides,
    )


def test_browser_auth_config_is_public_and_disabled_by_default():
    response = TestClient(app).get("/api/v1/auth/config")

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "client_id": None,
        "authority": None,
        "redirect_path": "/ui/index.html",
        "scopes": [],
    }


def test_browser_auth_config_returns_only_public_values():
    configured = settings(
        OIDC_ENABLED=True,
        OIDC_ISSUER="https://issuer.example/v2.0",
        OIDC_AUDIENCE="api-client-id",
        OIDC_JWKS_URL="https://issuer.example/keys",
        OIDC_BROWSER_ENABLED=True,
        OIDC_BROWSER_CLIENT_ID="spa-client-id",
        OIDC_BROWSER_AUTHORITY="https://issuer.example",
        OIDC_BROWSER_SCOPES="api://api-client-id/config.read, api://api-client-id/documents.extract",
    )
    app.dependency_overrides[get_settings] = lambda: configured
    try:
        response = TestClient(app).get("/api/v1/auth/config")
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert response.status_code == 200
    assert response.json() == {
        "enabled": True,
        "client_id": "spa-client-id",
        "authority": "https://issuer.example",
        "redirect_path": "/ui/index.html",
        "scopes": [
            "api://api-client-id/config.read",
            "api://api-client-id/documents.extract",
        ],
    }
    serialized = response.text.lower()
    assert "secret" not in serialized
    assert "jwks" not in serialized


def test_browser_auth_requires_complete_api_and_spa_configuration():
    with pytest.raises(ValidationError):
        settings(OIDC_BROWSER_ENABLED=True)
