# Security plan

## Phase 1: upload and resource protection

The extraction boundary enforces configured limits for upload size, filename length, PDF page count, image dimensions, and image pixel count. Supported file extensions are allowlisted and checked against file signatures. Temporary files are removed after processing or validation failure.

## Implemented security controls

- API-key and OIDC bearer authentication with scope-based authorization
- Tenant-aware processing history, review, retention, feedback export, and configuration operations
- Configurable rate limiting for extraction, API-key management, and read endpoints
- Trusted hosts, explicit CORS, proxy trust, and production documentation exposure settings
- Upload size, filename, PDF page, image dimension, pixel-count, extension, and signature validation
- Secret-safe security audit logging, bounded retention execution, and backup/restore helpers
- CI security regression coverage, Python/npm vulnerability audits, dependency review for pull requests, and SPDX SBOM generation

## Remaining operational decisions

- Select production-specific rate-limit storage, concurrency, and request-timeout policies from measured workload requirements.
- Complete deployment-specific monitoring, alert thresholds, incident response ownership, and disaster-recovery exercises.
- Keep asynchronous processing, retry guarantees, idempotency, and webhook security outside the current synchronous runtime contract until external integration requirements are concrete.

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
