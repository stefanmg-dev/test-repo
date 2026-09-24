from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from security_dependencies import (
    get_optional_api_key_principal,
    require_scope,
)
from security_principal import SecurityPrincipal


@pytest.mark.anyio
async def test_optional_api_key_principal_allows_missing_key():
    service = Mock()

    result = await get_optional_api_key_principal(
        api_key_service=service,
        api_key=None,
    )

    assert result is None
    service.authenticate.assert_not_called()


@pytest.mark.anyio
async def test_invalid_api_key_returns_401():
    service = Mock()
    service.authenticate.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await get_optional_api_key_principal(
            api_key_service=service,
            api_key="invalid",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {
        "WWW-Authenticate": "APIKey"
    }


@pytest.mark.anyio
async def test_scope_dependency_returns_401_403_or_principal():
    dependency = require_scope("documents:extract")
    principal = SecurityPrincipal(
        principal_type="service",
        subject="service-1",
        tenant_id="tenant-1",
        scopes=frozenset({"documents:extract"}),
    )
    assert await dependency(principal) is principal

    with pytest.raises(HTTPException) as unauthenticated:
        await dependency(None)
    assert unauthenticated.value.status_code == 401

    missing_scope = SecurityPrincipal(
        principal_type="service",
        subject="service-2",
        tenant_id="tenant-1",
        scopes=frozenset({"config:read"}),
    )
    with pytest.raises(HTTPException) as forbidden:
        await dependency(missing_scope)
    assert forbidden.value.status_code == 403
