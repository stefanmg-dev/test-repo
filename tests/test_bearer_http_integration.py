from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient

import api
import routes_extract
import security_scopes
from api import app
from oidc_token_validator import OidcTokenValidationError
from processing_run_dependencies import get_processing_run_service
from security_dependencies import (
    get_api_key_service,
    get_oidc_token_validator,
)
from security_principal import SecurityPrincipal


NOW = datetime(2026, 9, 25, tzinfo=timezone.utc)
VALID_TOKEN = "valid-bearer-token"
INVALID_TOKEN = "invalid-bearer-token"


class ApiKeyServiceStub:
    def authenticate(self, secret):
        return None


class OidcValidatorStub:
    def __init__(self, principal):
        self.principal = principal

    def validate(self, token):
        if token != VALID_TOKEN:
            raise OidcTokenValidationError("Invalid bearer token")
        return self.principal


class RecordingService:
    def __init__(self):
        self.run_id = uuid4()
        self.started = []
        self.list_calls = []

    def start_run(self, **kwargs):
        self.started.append(kwargs)
        return SimpleNamespace(id=self.run_id)

    def complete_run(self, run_id, **kwargs):
        return None

    def fail_run(self, run_id, **kwargs):
        return None

    def list_runs(self, **kwargs):
        self.list_calls.append(kwargs)
        return [], 0


def principal(*scopes):
    return SecurityPrincipal(
        principal_type="user",
        subject="entra-user-1",
        tenant_id="entra-tenant-1",
        scopes=frozenset(scopes),
    )


def install(service, configured_principal):
    app.dependency_overrides[get_processing_run_service] = lambda: service
    app.dependency_overrides[get_api_key_service] = lambda: ApiKeyServiceStub()
    app.dependency_overrides[get_oidc_token_validator] = (
        lambda: OidcValidatorStub(configured_principal)
    )


def bearer(token=VALID_TOKEN):
    return {"Authorization": f"Bearer {token}"}


def test_valid_bearer_scope_allows_history_and_propagates_tenant():
    service = RecordingService()
    install(service, principal("processing-runs:read"))

    response = TestClient(app).get(
        "/api/v1/processing-runs",
        headers=bearer(),
    )

    assert response.status_code == 200
    assert service.list_calls[0]["tenant_id"] == "entra-tenant-1"


def test_valid_bearer_without_required_scope_returns_403():
    service = RecordingService()
    install(service, principal("documents:extract"))

    response = TestClient(app).get(
        "/api/v1/processing-runs",
        headers=bearer(),
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Missing required scope: processing-runs:read"
    }


def test_invalid_bearer_returns_401():
    service = RecordingService()
    install(service, principal("processing-runs:read"))

    response = TestClient(app).get(
        "/api/v1/processing-runs",
        headers=bearer(INVALID_TOKEN),
    )

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_missing_credentials_return_401_when_legacy_access_is_disabled(
    monkeypatch,
):
    service = RecordingService()
    app.dependency_overrides[get_processing_run_service] = lambda: service
    app.dependency_overrides[get_api_key_service] = lambda: ApiKeyServiceStub()
    app.dependency_overrides[get_oidc_token_validator] = lambda: None
    monkeypatch.setattr(
        security_scopes,
        "get_settings",
        lambda: SimpleNamespace(
            legacy_anonymous_access_enabled=False,
        ),
    )

    response = TestClient(app).get("/api/v1/processing-runs")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_bearer_principal_is_persisted_as_processing_run_creator(
    monkeypatch,
):
    service = RecordingService()
    install(service, principal("documents:extract"))
    monkeypatch.setattr(
        routes_extract,
        "load_config",
        lambda: {
            "invoice": {
                "fields": [
                    {
                        "name": "invoice_number",
                        "type": "constant",
                        "value": "1",
                        "validation": [],
                    }
                ]
            }
        },
    )

    async def input_result(file):
        return {
            "text": "test text",
            "quality": {
                "status": "accepted",
                "requires_review": False,
                "input": {
                    "format": "PDF",
                    "source": "native_pdf",
                    "page_count": 1,
                },
                "warnings": [],
            },
        }

    monkeypatch.setattr(routes_extract, "extract_document_input", input_result)
    monkeypatch.setattr(routes_extract, "extract_values", lambda text: {})
    monkeypatch.setattr(
        routes_extract,
        "extract_document_data",
        lambda **kwargs: {
            "fields": {"invoice_number": "1"},
            "collections": {},
        },
    )
    monkeypatch.setattr(
        routes_extract,
        "validate_result",
        lambda **kwargs: {"valid": True, "errors": {}},
    )

    response = TestClient(app).post(
        "/extract-document",
        headers=bearer(),
        data={"document_type": "invoice"},
        files={"file": ("entra.pdf", b"test", "application/pdf")},
    )

    assert response.status_code == 200
    assert service.started[0]["tenant_id"] == "entra-tenant-1"
    assert service.started[0]["created_by_type"] == "user"
    assert service.started[0]["created_by_subject"] == "entra-user-1"


def test_public_operational_and_auth_configuration_routes_remain_public(
    monkeypatch,
):
    monkeypatch.setattr(
        api,
        "validate_database_startup",
        lambda engine: SimpleNamespace(
            database_connected=True,
            current_revisions=("revision",),
            expected_revisions=("revision",),
        ),
    )
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/ready").status_code == 200
    assert client.get("/api/v1/auth/config").status_code == 200
    assert client.get("/ui/index.html").status_code == 200
