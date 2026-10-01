# Production deployment smoke test

## Purpose

This runbook is the binary go/no-go check after a production deployment or rollback. It is intentionally read-only and shallow. It verifies liveness, readiness, migration parity, public browser-auth configuration, authentication enforcement, and an authenticated processing-history read.

It does not replace the full regression suite, backup restore verification, penetration testing, or representative document extraction testing.

## Preconditions

- The deployment uses the intended immutable image and commit.
- Database migrations completed as a separate release step before application traffic was enabled.
- The production hostname uses HTTPS.
- Secrets are supplied by the deployment secret mechanism, not command history or committed files.
- A dedicated read-only smoke API key or OIDC identity exists when authenticated validation is required.
- The smoke identity belongs to a dedicated smoke tenant and has only `processing-runs:read`.

## Automated read-only smoke helper

The helper never sends document content and never performs POST, PUT, PATCH, or DELETE requests.

Anonymous enforcement check:

```bash
python scripts/deployment_smoke.py \
  --base-url "https://production.example.com"
```

The anonymous mode requires:

- `/health` returns HTTP 200 with `{"status":"ok"}`;
- `/ready` returns HTTP 200 with connected database, current migrations, and a revision;
- `/api/v1/auth/config` returns a public JSON configuration;
- `/api/v1/processing-runs?offset=0&limit=1` returns HTTP 401.

Authenticated API-key check:

```bash
python scripts/deployment_smoke.py \
  --base-url "https://production.example.com" \
  --api-key "$SMOKE_API_KEY"
```

Authenticated bearer-token check:

```bash
python scripts/deployment_smoke.py \
  --base-url "https://production.example.com" \
  --bearer-token "$SMOKE_BEARER_TOKEN"
```

Authenticated mode requires processing history to return HTTP 200 with an `items` array. Supply exactly one authentication mechanism. The helper refuses non-HTTPS base URLs and never prints credentials.

## Microsoft Entra browser smoke checklist

When browser OIDC is enabled:

1. Open `/ui/index.html` in a clean browser session.
2. Confirm unauthenticated protected API calls do not expose data.
3. Complete sign-in with the dedicated smoke identity.
4. Confirm configuration and Processing History load according to delegated scopes.
5. Confirm sign-out removes the active browser session from the application UI.
6. Confirm no client secret is present in browser requests, source, or storage.

This browser check validates the configured redirect URI, authority, client ID, delegated scopes, consent, token acquisition, and protected API call path.

## Tenant-isolation smoke checklist

Tenant isolation requires two pre-created read-only smoke identities, Tenant A and Tenant B, plus a known non-sensitive smoke run owned by Tenant A.

1. Tenant A can retrieve the known Tenant A run.
2. Tenant B cannot retrieve the Tenant A run and receives the documented not-found response.
3. Tenant B list results do not contain the Tenant A run identifier.
4. Neither identity has write, review, retention, export, configuration-write, or admin scopes.
5. Do not create or upload production documents solely for this check.

The automated helper does not accept run identifiers and does not automate this cross-tenant check, preventing accidental disclosure in command output.

## Operational checks

- Confirm application replicas are ready before traffic is enabled.
- Confirm startup logs contain no migration mismatch, database connectivity failure, repeated restart, or secret value.
- Confirm request IDs are present for smoke requests.
- Confirm error rate, latency, CPU, memory, database connections, and restart count remain within the deployment's approved operating thresholds.
- Confirm public API documentation remains disabled when `EXPOSE_API_DOCS=false`.
- Confirm rate limiting and trusted-host configuration match the production environment.

## Go criteria

Mark the deployment successful only when:

- migrations completed successfully;
- every automated smoke assertion passed;
- the selected authentication mode passed;
- browser OIDC passed when enabled;
- tenant isolation passed when required for the release;
- no critical application, database, authentication, or security-audit errors appeared;
- the rollback path and previous known-good image remain available.

## No-go and rollback criteria

Stop routing new traffic or begin rollback when any of these is true:

- `/health` is unavailable;
- `/ready` is not HTTP 200, database is disconnected, or migrations are not current;
- anonymous access can read a protected endpoint;
- valid smoke credentials cannot read their permitted endpoint;
- tenant isolation fails;
- replicas repeatedly restart;
- application logs expose secrets or show persistent unhandled failures;
- the deployed image or migration revision does not match the approved release.

Rollback the application image through the deployment platform's established mechanism. Do not downgrade the database blindly. If the release contains a non-backward-compatible migration, follow the migration-specific recovery plan and preserve diagnostic evidence.

## Evidence

Record only:

- deployment commit and image digest;
- migration revision;
- UTC start and completion timestamps;
- smoke result by check name;
- operator or automation identity;
- rollback decision and incident reference when applicable.

Do not record API keys, bearer tokens, document values, filenames, raw OCR, tenant secrets, or complete processing-run payloads.

## Related operational documentation

- [System architecture](architecture.md)
- [Production deployment](deployment.md)
- [Security plan](security.md)
- [PostgreSQL backup and restore runbook](backup-restore.md)
