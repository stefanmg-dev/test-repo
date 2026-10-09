# Local development start, status, and stop

This is the single operational entry point for local development after a Mac restart. PostgreSQL runs as a Homebrew service. Uvicorn runs in the foreground so its logs remain visible and `Ctrl+C` stops it predictably.

## Recommended workflow after a restart

Open Terminal and run:

```bash
cd ~/AI/ai-code-assistant
pipenv run bash scripts/local_dev.sh start
```

The helper supplies the local Unix-socket `DATABASE_URL`, verifies PostgreSQL, applies pending Alembic migrations, and starts Uvicorn at `127.0.0.1:8000`.

Keep that terminal open. The UI is available at:

- `http://127.0.0.1:8000/ui/test.html`
- `http://127.0.0.1:8000/ui/history.html`

## Check status from a second terminal

```bash
cd ~/AI/ai-code-assistant
pipenv run bash scripts/local_dev.sh status
```

This reports the Git checkpoint, Python executable, PostgreSQL readiness, Alembic revision, recorded Uvicorn process, and the `/health` and `/ready` responses.

## Stop the API

Preferred when the Uvicorn terminal is visible:

```text
Ctrl+C
```

From another terminal, when the API was started by the helper:

```bash
cd ~/AI/ai-code-assistant
pipenv run bash scripts/local_dev.sh stop
```

PostgreSQL normally remains running as a Homebrew service.

## Database-only check

```bash
cd ~/AI/ai-code-assistant
pipenv run bash scripts/local_dev.sh check
```

## If PostgreSQL is not running

```bash
brew services start postgresql@17
pg_isready
```

Then run the start command again.

## Understand the local development layers

These are separate parts of the local environment:

- **Terminal** is the shell window where commands run. Opening a new Terminal does not automatically activate Pipenv, export `DATABASE_URL`, or start Uvicorn.
- **Pipenv environment** selects the project Python interpreter and installed dependencies. `pipenv run <command>` runs one command in that environment without opening an interactive subshell.
- **`DATABASE_URL`** tells the application and database tools which PostgreSQL database to use. A manual `export` affects only the current terminal session.
- **Uvicorn** is the running API server. Uvicorn is needed when using the browser UI or making HTTP requests to the API, but it is not required for Git commands or most test commands.

## Standard bootstrap in a new Terminal

For Git operations and tests, use the project directory and run commands through Pipenv:

```bash
cd ~/AI/ai-code-assistant
export DATABASE_URL='postgresql+psycopg:///document_processing?host=/tmp'
pipenv run python -m pytest -q
```

The application does not need to be running for `git status`, `git diff`, `git add`, `git commit`, `git push`, or the normal pytest suite.

Use the helper when the browser UI or live API is needed:

```bash
cd ~/AI/ai-code-assistant
pipenv run bash scripts/local_dev.sh start
```

The helper supplies its own default `DATABASE_URL`, checks PostgreSQL, applies migrations, and starts Uvicorn.

## Why the server terminal appears blocked

`scripts/local_dev.sh start` runs Uvicorn in the foreground and waits for the server process. The terminal therefore shows server logs instead of a new shell prompt. This is expected and does not mean the terminal has frozen.

Keep the server terminal open while using the UI. Run Git commands, tests, and status checks in a second Terminal. Press `Ctrl+C` in the server terminal to stop Uvicorn and return to the prompt.

## Manual fallback

Use this only when debugging the helper itself:

```bash
cd ~/AI/ai-code-assistant
pipenv shell
export DATABASE_URL='postgresql+psycopg:///document_processing?host=/tmp'
alembic upgrade head
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

Leave a Pipenv subshell with `exit` or `Ctrl+D`. Do not run `pipenv shell` from an already active virtual environment. Do not use bare `pkill`; it requires a process pattern and can target unrelated processes.

## Environment lifetime

`DATABASE_URL` exported manually applies only to the current shell. The helper avoids that problem by supplying the local default on every invocation. It does not create or modify `.env`.
