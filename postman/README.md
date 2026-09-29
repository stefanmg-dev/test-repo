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

## Universal Invoice feedback export

The `02 Processing History` folder contains two read-only JSONL requests:

1. Run `Universal Invoice Feedback Export - First Page` with `feedback_export_limit` set from 1 through 1000.
2. If both `X-Next-Reviewed-At` and `X-Next-Processing-Run-Id` are returned, Postman stores them as a paired tuple cursor.
3. Run `Universal Invoice Feedback Export - Resume` to continue after that tuple. Both cursor components must be supplied together.
4. Repeat the resume request while both next-cursor headers are returned. A response without those headers is the final page.

An empty eligible dataset returns an empty JSONL body and no next-cursor headers. Every JSONL record uses `feedback_schema_version` `1`. The committed environment keeps cursor variables empty and does not contain API keys, document values, filenames, raw OCR text, or other secrets.
