from typing import Any

import jwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

from app_settings import AppSettings
from oidc_scope_mapping import normalize_oidc_scopes
from security_principal import SecurityPrincipal


class OidcTokenValidationError(ValueError):
    pass


class OidcTokenValidator:
    def __init__(
        self,
        settings: AppSettings,
        *,
        jwks_client: PyJWKClient | None = None,
    ):
        if not settings.oidc_enabled:
            raise ValueError("OIDC validation is not enabled")
        self._settings = settings
        self._jwks_client = jwks_client or PyJWKClient(
            settings.oidc_jwks_url,
            cache_keys=True,
        )

    def validate(self, token: str) -> SecurityPrincipal:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=self._settings.oidc_algorithms_list(),
                audience=self._settings.oidc_audience,
                issuer=self._settings.oidc_issuer,
                options={
                    "require": ["exp", "iat", "iss", "aud"],
                },
            )
        except (InvalidTokenError, ValueError) as exc:
            raise OidcTokenValidationError("Invalid bearer token") from exc

        return self._build_principal(claims)

    def _build_principal(
        self,
        claims: dict[str, Any],
    ) -> SecurityPrincipal:
        tenant_id = claims.get(self._settings.oidc_tenant_claim)
        subject = claims.get(self._settings.oidc_subject_claim)
        if not isinstance(tenant_id, str) or not tenant_id:
            raise OidcTokenValidationError("Bearer token has no tenant claim")
        if not isinstance(subject, str) or not subject:
            raise OidcTokenValidationError("Bearer token has no subject claim")

        raw_scopes = claims.get(self._settings.oidc_scopes_claim, "")
        if isinstance(raw_scopes, str):
            scopes = normalize_oidc_scopes(raw_scopes.split())
        elif isinstance(raw_scopes, list) and all(
            isinstance(value, str) for value in raw_scopes
        ):
            scopes = normalize_oidc_scopes(raw_scopes)
        else:
            raise OidcTokenValidationError("Bearer token has invalid scopes")

        return SecurityPrincipal(
            principal_type="user",
            subject=subject,
            tenant_id=tenant_id,
            scopes=scopes,
        )
