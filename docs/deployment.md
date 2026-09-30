# Production container foundation

## Runtime model

The API runs as one non-root Uvicorn process in a Linux container. PostgreSQL is an external dependency. The image contains Poppler, CPU-only PyTorch, and the EasyOCR Bulgarian and English models.

## Build

```bash
docker build --tag document-processing-api:local .
```

The build preloads EasyOCR models. Runtime model downloads are disabled.

## Database migrations

Run migrations as a separate release step before starting API replicas:

```bash
docker run --rm \
  --env-file .env.production \
  document-processing-api:local \
  /app/scripts/container_migrate.sh
```

Do not run migrations concurrently from every API replica.

## Start

```bash
docker run --rm \
  --env-file .env.production \
  --publish 8000:8000 \
  document-processing-api:local
```

The container runs as UID and GID `10001`. `/tmp` is used for temporary uploaded documents and generated PDF page images. Uploaded documents are not persistent container data.

## Health contracts

- `GET /health` is the Docker liveness check and does not query PostgreSQL.
- `GET /ready` checks PostgreSQL connectivity and Alembic revision parity.

## Required deployment order

1. Provision PostgreSQL without exposing it publicly.
2. Inject production environment values through the deployment secret mechanism.
3. Run `/app/scripts/container_migrate.sh` once.
4. Start the API container.
5. Wait for `GET /ready` to return HTTP 200 before routing traffic.

## Security boundary

The image excludes local environment files, invoices, uploaded documents, local databases, test caches, AI model directories, Postman assets, and Git metadata. The runtime includes API-key and OIDC authentication, scope-based authorization, tenant-aware access control, upload validation and resource limits, configurable rate limiting, trusted-host enforcement, explicit CORS configuration, proxy trust settings, security audit logging, retention controls, and production API documentation exposure settings. Production deployments must configure these controls explicitly through the deployment secret and environment mechanism.

## Network and API boundary

- Set `ALLOWED_HOSTS` to the public API hostname and any internal health-check hostname.
- Keep `CORS_ALLOWED_ORIGINS` empty for the bundled same-origin UI.
- If a separate browser frontend is deployed, list only its explicit HTTPS origins.
- Keep `EXPOSE_API_DOCS=false` in production until authenticated documentation is implemented.
- Set `FORWARDED_ALLOW_IPS` only to the trusted reverse proxy or load balancer addresses.
- TLS terminates at the trusted ingress or reverse proxy. The application does not force HTTPS redirects internally.

## Browser authentication asset

The versioned `ui/auth.bundle.js` file is built from `ui/auth.js` with the locked npm dependencies. CI runs `npm ci`, rebuilds the bundle, and fails when the committed bundle or lock file is stale. The production image consumes the verified versioned asset and does not require Node.js at runtime.

## Microsoft Entra production cutover

Use two Microsoft Entra app registrations: one resource application for the API and one public client application for the browser SPA.

### API application

1. Record the tenant ID and API application client ID.
2. Keep the Application ID URI as `api://<API_CLIENT_ID>` unless the deployment uses another verified unique URI.
3. Expose `documents.extract`, `processing-runs.read`, `config.read`, and `config.write`.
4. Do not expose the internal `admin` permission as a delegated browser scope.
5. Use the API application client ID as `OIDC_AUDIENCE`.

### Browser SPA application

1. Configure the application as a Single-page application.
2. Register the exact HTTPS redirect URI `<PUBLIC_ORIGIN>/ui/index.html`.
3. Add delegated permissions for all four API scopes.
4. Grant tenant admin consent when required by tenant policy.
5. Use the SPA application client ID as `OIDC_BROWSER_CLIENT_ID`.

### Production environment

Replace every `your-*` placeholder in `.env.production.example`, then initially set:

```text
OIDC_ENABLED=true
OIDC_BROWSER_ENABLED=true
LEGACY_ANONYMOUS_ACCESS_ENABLED=true
```

Confirm interactive sign-in, silent token acquisition, extraction, history reads, configuration reads, and configuration writes. Inspect the access token and confirm `iss`, `aud`, `tid`, `sub`, `exp`, `iat`, and `scp` match the configured API contract.

Only after the authenticated smoke test succeeds, set `LEGACY_ANONYMOUS_ACCESS_ENABLED=false`. Redeploy and verify protected routes return HTTP 401 without credentials while `/health`, `/ready`, `/api/v1/auth/config`, and static UI assets remain public.

## Processing run retention

Set `PROCESSING_RUN_RETENTION_DAYS` to the minimum completed-run age eligible for retention. The default is 365 days; accepted values are 30 through 3650.

Retention is tenant-aware and requires an authenticated principal with the internal `admin` scope. Browser delegated scopes do not include `admin`.

Use the endpoints in this order:

1. Call `GET /api/v1/processing-runs/retention-preview` and review the cutoff, candidate count, and candidate date range.
2. Call `POST /api/v1/processing-runs/retention-execute` only after validating the preview.
3. Send the exact confirmation value `DELETE` and a batch limit from 1 through 1000.
4. Repeat preview before any additional batch.

Execution permanently deletes at most the requested number of the oldest eligible processing runs. Runs still processing and runs with pending review are excluded. Execution is atomic and emits security audit metadata containing the tenant identity, cutoff, limit, and deleted count, without document values.

Do not schedule retention automatically until operational monitoring, backup, and restore procedures have been validated.
