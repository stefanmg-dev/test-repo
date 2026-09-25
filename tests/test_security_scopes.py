from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from security_principal import SecurityPrincipal
from security_scopes import (
    CONFIG_READ,
    CONFIG_WRITE,
    DOCUMENTS_EXTRACT,
    PROCESSING_RUNS_READ,
    enforce_config_scope,
    enforce_scope_if_authenticated,
)


def principal(*scopes):
    return SecurityPrincipal(
        principal_type="service",
        subject="service-1",
        tenant_id="tenant-1",
        scopes=frozenset(scopes),
    )


def test_legacy_anonymous_access_remains_allowed_during_transition():
    enforce_scope_if_authenticated(None, DOCUMENTS_EXTRACT)


def test_authenticated_principal_requires_explicit_scope():
    with pytest.raises(HTTPException) as exc_info:
        enforce_scope_if_authenticated(
            principal(PROCESSING_RUNS_READ),
            DOCUMENTS_EXTRACT,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Missing required scope: documents:extract"
    )


def test_explicit_scope_and_admin_are_allowed():
    enforce_scope_if_authenticated(
        principal(DOCUMENTS_EXTRACT),
        DOCUMENTS_EXTRACT,
    )
    enforce_scope_if_authenticated(
        principal("admin"),
        DOCUMENTS_EXTRACT,
    )


@pytest.mark.anyio
async def test_configuration_scope_is_selected_from_http_method():
    await enforce_config_scope(
        SimpleNamespace(method="GET"),
        principal(CONFIG_READ),
    )
    await enforce_config_scope(
        SimpleNamespace(method="POST"),
        principal(CONFIG_WRITE),
    )

    with pytest.raises(HTTPException) as exc_info:
        await enforce_config_scope(
            SimpleNamespace(method="DELETE"),
            principal(CONFIG_READ),
        )
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "Missing required scope: config:write"
    )
