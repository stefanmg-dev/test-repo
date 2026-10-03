# Development Quick Reference

For human-review semantics, see [Human review acceptance contract](human-review-acceptance-contract.md).


For processing outcome semantics, see [Processing acceptance contract](processing-acceptance-contract.md).


For real-document acceptance, see [Real-document fixture matrix and acceptance checklist](real-document-fixture-matrix.md).


For the complete restart-safe start, status, and stop workflow, see [Local development start, status, and stop](local-development-runbook.md).


## Enter the project

```bash
cd ~/AI/ai-code-assistant
pipenv shell
```

The prompt should begin with `(ai-code-assistant)`. For a single command without an interactive shell, use `pipenv run <command>`.

## Configure the local database for the current shell

```bash
export DATABASE_URL='postgresql+psycopg:///document_processing?host=/tmp'
pg_isready
python -c 'from app_settings import get_settings; print("settings OK")'
```

This local URL uses the PostgreSQL Unix socket and contains no password. The export applies only to the current shell. Do not create `.env` by copying placeholder credentials from `.env.example`.

## Start the local API and UI

```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Keep that terminal open. The UI is available at `http://127.0.0.1:8000/ui/test.html` only while Uvicorn is running. Use `Ctrl+C` to stop the server.

## Check the service

```bash
curl --connect-timeout 2 --max-time 10 http://127.0.0.1:8000/health
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

## Export OpenAPI

```bash
python scripts/export_openapi.py
```

## Run tests

```bash
PYTHONPATH=. pytest
```

## Check database migrations

```bash
alembic check
```

## Final verification

```bash
python scripts/export_openapi.py
PYTHONPATH=. pytest
alembic check
git diff --check
git diff --stat
git status --short
```
