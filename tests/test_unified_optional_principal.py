from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from oidc_token_validator import OidcTokenValidationError
from security_dependencies import get_optional_principal
from security_principal import SecurityPrincipal


API_PRINCIPAL = SecurityPrincipal(
    principal_type="service",
    subject="service-1",
    tenant_id="tenant-1",
    scopes=frozenset({"documents:extract"}),
)
OIDC_PRINCIPAL = SecurityPrincipal(
    principal_type="user",
    subject="user-1",
    tenant_id="tenant-1",
    scopes=frozenset({"processing-runs:read"}),
)


def bearer(token="token"):
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


@pytest.mark.anyio
async def test_returns_none_without_credentials():
    result = await get_optional_principal(
        api_key_service=Mock(),
        oidc_validator=None,
        api_key=None,
        bearer=None,
    )
    assert result is None


@pytest.mark.anyio
async def test_authenticates_api_key():
    api_key_service = Mock()
    api_key_service.authenticate.return_value = API_PRINCIPAL

    result = await get_optional_principal(
        api_key_service=api_key_service,
        oidc_validator=None,
        api_key="dpk_prefix_secret",
        bearer=None,
    )

    assert result is API_PRINCIPAL


@pytest.mark.anyio
async def test_authenticates_bearer_token():
    validator = Mock()
    validator.validate.return_value = OIDC_PRINCIPAL

    result = await get_optional_principal(
        api_key_service=Mock(),
        oidc_validator=validator,
        api_key=None,
        bearer=bearer(),
    )

    assert result is OIDC_PRINCIPAL
    validator.validate.assert_called_once_with("token")


@pytest.mark.anyio
async def test_rejects_both_authentication_mechanisms():
    with pytest.raises(HTTPException) as exc_info:
        await get_optional_principal(
            api_key_service=Mock(),
            oidc_validator=Mock(),
            api_key="dpk_prefix_secret",
            bearer=bearer(),
        )
    assert exc_info.value.status_code == 400


@pytest.mark.anyio
async def test_rejects_bearer_when_oidc_is_disabled():
    with pytest.raises(HTTPException) as exc_info:
        await get_optional_principal(
            api_key_service=Mock(),
            oidc_validator=None,
            api_key=None,
            bearer=bearer(),
        )
    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.anyio
async def test_rejects_invalid_bearer_token():
    validator = Mock()
    validator.validate.side_effect = OidcTokenValidationError(
        "invalid"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_optional_principal(
            api_key_service=Mock(),
            oidc_validator=validator,
            api_key=None,
            bearer=bearer("invalid"),
        )
    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
