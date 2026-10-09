from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
RUNBOOK = ROOT / "docs" / "local-development-runbook.md"
SCRIPT = ROOT / "scripts" / "local_dev.sh"
QUICK_REFERENCE = (
    ROOT / "docs" / "development-quick-reference.md"
)


def test_runbook_documents_restart_safe_workflow():
    content = RUNBOOK.read_text(encoding="utf-8")

    assert (
        "pipenv run bash scripts/local_dev.sh start"
        in content
    )
    assert (
        "pipenv run bash scripts/local_dev.sh status"
        in content
    )
    assert (
        "pipenv run bash scripts/local_dev.sh stop"
        in content
    )
    assert "brew services start postgresql@17" in content
    assert "Ctrl+C" in content
    assert "Do not use bare `pkill`" in content


def test_local_helper_has_operational_commands():
    content = SCRIPT.read_text(encoding="utf-8")

    for command in (
        "start)",
        "status)",
        "stop)",
        "check)",
    ):
        assert command in content

    assert "alembic upgrade head" in content
    assert "pg_isready" in content
    assert "uvicorn api:app --reload" in content
    assert "DATABASE_URL" in content


def test_quick_reference_links_operational_runbook():
    content = QUICK_REFERENCE.read_text(
        encoding="utf-8"
    )

    assert "](local-development-runbook.md)" in content

def test_status_handles_stopped_api_without_raw_curl_errors():
    content = SCRIPT.read_text(encoding="utf-8")

    assert "2>/dev/null" in content
    assert (
        "API is not reachable on 127.0.0.1:8000."
        in content
    )


def test_runbook_explains_local_environment_layers():
    content = RUNBOOK.read_text(encoding="utf-8")

    assert "Opening a new Terminal does not automatically" in content
    assert "**Pipenv environment**" in content
    assert "**`DATABASE_URL`**" in content
    assert "**Uvicorn**" in content
    assert "not required for Git commands or most test commands" in content


def test_runbook_documents_new_terminal_bootstrap():
    content = RUNBOOK.read_text(encoding="utf-8")

    assert "## Standard bootstrap in a new Terminal" in content
    assert "cd ~/AI/ai-code-assistant" in content
    assert "postgresql+psycopg:///document_processing?host=/tmp" in content
    assert "pipenv run python -m pytest -q" in content
    assert "The application does not need to be running" in content


def test_runbook_explains_foreground_server_terminal():
    content = RUNBOOK.read_text(encoding="utf-8")

    assert "## Why the server terminal appears blocked" in content
    assert "runs Uvicorn in the foreground" in content
    assert "does not mean the terminal has frozen" in content
    assert "in a second Terminal" in content
    assert "Press `Ctrl+C`" in content

