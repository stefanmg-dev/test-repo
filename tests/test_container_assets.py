from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_has_production_runtime_contract():
    dockerfile = read("Dockerfile")

    assert "FROM python:3.14-slim" in dockerfile
    assert "poppler-utils" in dockerfile
    assert "download.pytorch.org/whl/cpu" in dockerfile
    assert "preload_easyocr_models.py" in dockerfile
    assert "EASYOCR_DOWNLOAD_ENABLED=false" in dockerfile
    assert "USER 10001:10001" in dockerfile
    assert "/health" in dockerfile
    assert 'CMD ["/app/scripts/container_start.sh"]' in dockerfile


def test_dockerignore_excludes_sensitive_local_assets():
    ignored = {
        line.strip()
        for line in read(".dockerignore").splitlines()
        if line.strip()
    }

    assert {
        ".git",
        ".env",
        "uploaded_documents",
        "models",
        ".EasyOCR",
        "*.pdf",
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.db",
        "tests",
    } <= ignored


def test_container_scripts_keep_migrations_separate():
    start = read("scripts/container_start.sh")
    migrate = read("scripts/container_migrate.sh")

    assert "uvicorn api:app" in start
    assert "alembic upgrade" not in start
    assert "alembic upgrade head" in migrate


def test_production_environment_template_is_safe():
    template = read(".env.production.example")

    assert "ENVIRONMENT=production" in template
    assert "EASYOCR_DOWNLOAD_ENABLED=false" in template
    assert "EXPOSE_API_DOCS=false" in template
    assert "ALLOWED_HOSTS=api.example.com" in template
    assert "localhost" not in template
    assert "/Users/" not in template
    assert "change_me" in template


def test_linux_sqlalchemy_runtime_dependency_is_explicit():
    pipfile = read("Pipfile")

    assert "greenlet" in pipfile


def test_versioned_browser_auth_assets_exist():
    for asset in (
        "package.json",
        "package-lock.json",
        "ui/auth.js",
        "ui/auth.bundle.js",
        "ui/auth-controls.js",
    ):
        assert (ROOT / asset).is_file(), asset
