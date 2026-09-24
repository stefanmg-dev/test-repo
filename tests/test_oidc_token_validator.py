from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app_settings import AppSettings
from oidc_token_validator import (
    OidcTokenValidationError,
    OidcTokenValidator,
)


ISSUER = "https://issuer.example/tenant/v2.0"
AUDIENCE = "api-client-id"


def settings(**overrides):
    return AppSettings(
        _env_file=None,
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
        OIDC_ENABLED=True,
        OIDC_ISSUER=ISSUER,
        OIDC_AUDIENCE=AUDIENCE,
        OIDC_JWKS_URL="https://issuer.example/keys",
        **overrides,
    )


def signed_token(private_key, **claim_overrides):
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(minutes=5),
        "tid": "tenant-1",
        "sub": "user-1",
        "scp": "documents:extract processing-runs:read",
        **claim_overrides,
    }
    return jwt.encode(claims, private_key, algorithm="RS256")


def validator(private_key, configured=None):
    key = Mock()
    key.key = private_key.public_key()
    client = Mock()
    client.get_signing_key_from_jwt.return_value = key
    return OidcTokenValidator(
        configured or settings(),
        jwks_client=client,
    )


def test_validates_token_and_builds_user_principal():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    principal = validator(private_key).validate(
        signed_token(private_key)
    )

    assert principal.principal_type == "user"
    assert principal.subject == "user-1"
    assert principal.tenant_id == "tenant-1"
    assert principal.scopes == frozenset(
        {"documents:extract", "processing-runs:read"}
    )


@pytest.mark.parametrize(
    "claim_overrides",
    [
        {"aud": "wrong-audience"},
        {"iss": "https://wrong.example"},
        {"exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
    ],
)
def test_rejects_invalid_standard_claims(claim_overrides):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with pytest.raises(OidcTokenValidationError):
        validator(private_key).validate(
            signed_token(private_key, **claim_overrides)
        )


def test_rejects_missing_tenant_or_subject():
    configured = settings(
        OIDC_TENANT_CLAIM="tenant",
        OIDC_SUBJECT_CLAIM="subject",
    )
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with pytest.raises(OidcTokenValidationError):
        validator(private_key, configured).validate(
            signed_token(private_key)
        )
