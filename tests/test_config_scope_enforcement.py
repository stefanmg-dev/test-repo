import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import config_store

from api import app
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


@pytest.fixture
def isolated_config(tmp_path, monkeypatch):
    config_path = tmp_path / "document_types.json"
    shutil.copy(
        Path("document_types.json"),
        config_path,
    )
    monkeypatch.setattr(
        config_store,
        "CONFIG_PATH",
        config_path,
    )
    return config_path


def principal(*scopes):
    return SecurityPrincipal(
        principal_type="user",
        subject="user-1",
        tenant_id="tenant-1",
        scopes=frozenset(scopes),
    )


def install(configured_principal):
    app.dependency_overrides[get_optional_principal] = (
        lambda: configured_principal
    )


def test_config_read_requires_read_scope_for_authenticated_principal(
    isolated_config,
):
    install(principal("config:write"))

    response = TestClient(app).get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Missing required scope: config:read"
    }


def test_config_read_accepts_read_scope(isolated_config):
    install(principal("config:read"))

    response = TestClient(app).get(
        "/api/v1/config/document-types"
    )

    assert response.status_code == 200


def test_config_write_requires_write_scope(isolated_config):
    install(principal("config:read"))

    response = TestClient(app).post(
        "/api/v1/config/document-types",
        json={
            "document_type": "scope_test",
            "configuration_mode": "legacy",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Missing required scope: config:write"
    }


def test_config_write_accepts_write_scope(isolated_config):
    install(principal("config:write"))

    response = TestClient(app).post(
        "/api/v1/config/document-types",
        json={
            "document_type": "scope_test",
            "configuration_mode": "legacy",
        },
    )

    assert response.status_code == 201


def test_config_admin_and_legacy_access_remain_compatible(
    isolated_config,
):
    install(principal("admin"))
    assert TestClient(app).get(
        "/api/v1/config/document-types"
    ).status_code == 200

    install(None)
    assert TestClient(app).get(
        "/api/v1/config/document-types"
    ).status_code == 200
