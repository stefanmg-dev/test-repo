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

The image excludes local environment files, invoices, uploaded documents, local databases, test caches, AI model directories, Postman assets, and Git metadata. Authentication, authorization, upload limits, rate limiting, and production HTTP hardening are separate planned security packages.
