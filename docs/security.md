# Security plan

## Phase 1: upload and resource protection

The extraction boundary enforces configured limits for upload size, filename length, PDF page count, image dimensions, and image pixel count. Supported file extensions are allowlisted and checked against file signatures. Temporary files are removed after processing or validation failure.

## Planned phases

- Authentication and object/function-level authorization
- Rate limiting, concurrency limits, and request timeouts
- Trusted hosts, explicit CORS, proxy trust, and production documentation exposure
- Retention, privacy, audit trail, backup protection, and deletion workflows
- Dependency scanning and security regression automation

## Network and API hardening

Production uses an explicit host allowlist, disables public OpenAPI and interactive documentation, and leaves CORS disabled by default. Cross-origin browser access is enabled only through explicit origins. Forwarded headers are trusted only from deployment-configured proxy addresses.

## Legacy anonymous access transition

`LEGACY_ANONYMOUS_ACCESS_ENABLED` defaults to `true` while the browser UI has no OIDC sign-in flow. Setting it to `false` requires authentication for extraction, processing history, and configuration API operations. Health, readiness, and static UI assets remain public. Production deployments should switch it to `false` only after browser authentication is configured and tested.

## Browser OIDC configuration

`GET /api/v1/auth/config` exposes only public SPA configuration. Browser OIDC remains disabled by default. Enabling it requires the API OIDC validator settings plus the SPA client ID, authority, redirect path, and delegated API scopes. No client secret, token, JWKS URL, or private credential is returned to the browser.

## OIDC delegated scope boundary

Microsoft Entra delegated scopes are mapped through an explicit allowlist:

```text
documents.extract    -> documents:extract
processing-runs.read -> processing-runs:read
config.read           -> config:read
config.write          -> config:write
```

Unknown delegated scopes are ignored. The internal `admin` permission is not granted from the OIDC `scp` claim. API-key scopes keep their existing internal names.

## Authentication cutover gate

Do not disable legacy anonymous access until the production SPA redirect URI, delegated permissions, admin consent, token claims, and authenticated API calls have been verified. Roll back by restoring `LEGACY_ANONYMOUS_ACCESS_ENABLED=true`; do not weaken issuer, audience, signature, or scope validation.
