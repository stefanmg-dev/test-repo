# Postman package

## Import

Import `Document_Processing_API_Stable.postman_collection.json` and `Document_Processing_Local.postman_environment.json`, then select `Document Processing Local`.

Populate local file paths only in Postman. Never commit absolute paths, invoices, raw extraction responses, credentials, or personal data.

## Confirmed manually

Health; A1, Electrohold, and Toplofikacia extraction; processing history list/detail and filters; unsupported file 415; unknown document type 404; missing file 422; processing run not found 404; read-only configuration.

## Pending manual fixtures

Generic fallback and corrupted PDF 422 remain defined with empty path variables.

## Health endpoints

- `GET /health` is a low-cost liveness check and does not query PostgreSQL.
- `GET /ready` verifies PostgreSQL connectivity and the current Alembic revision.

## Processing run retention

The `02 Processing History` folder includes admin-only retention preview and execution requests.

Set `admin_api_key` in the selected local Postman environment. Keep it empty in the committed environment file and never commit a real credential.

Run `Retention Preview` first. Review the returned cutoff and candidate count. Run `Retention Execute` only when deletion is intended; it sends the exact confirmation value `DELETE` and uses `retention_limit`, which defaults to 100. Execution is irreversible and deletes no more than 1000 eligible rows per request.
