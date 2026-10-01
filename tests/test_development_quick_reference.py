from pathlib import Path


REFERENCE = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "development-quick-reference.md"
)


def test_development_quick_reference_contains_core_commands():
    content = REFERENCE.read_text(encoding="utf-8")
    for command in (
        "pipenv shell",
        "export DATABASE_URL=",
        "pg_isready",
        "uvicorn api:app --reload",
        "python scripts/export_openapi.py",
        "PYTHONPATH=. pytest",
        "alembic check",
        "git diff --check",
        "git status --short",
    ):
        assert command in content


def test_development_quick_reference_warns_about_runtime_and_placeholders():
    content = REFERENCE.read_text(encoding="utf-8")
    assert "only while Uvicorn is running" in content
    assert "Do not create `.env`" in content
    assert "placeholder credentials" in content
