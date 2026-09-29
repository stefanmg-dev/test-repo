from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP = PROJECT_ROOT / "scripts" / "postgres_backup.sh"
RESTORE = PROJECT_ROOT / "scripts" / "postgres_restore_verify.sh"
GITIGNORE = PROJECT_ROOT / ".gitignore"
DOCKERIGNORE = PROJECT_ROOT / ".dockerignore"


def read(path):
    return path.read_text(encoding="utf-8")


def test_backup_uses_custom_archive_and_refuses_overwrite():
    content = read(BACKUP)

    assert "set -eu" in content
    assert "--format=custom" in content
    assert 'if [ -e "$BACKUP_FILE" ]' in content
    assert "pg_restore --list" in content
    assert "--no-owner" in content
    assert "--no-privileges" in content


def test_restore_has_explicit_non_production_guards():
    content = read(RESTORE)

    assert 'RESTORE_CONFIRM" != "RESTORE"' in content
    assert "*_restore|*_test" in content
    assert "Source and restore databases must be different" in content
    assert "Restore destination must be an empty database" in content
    assert "--exit-on-error" in content
    assert "validate_database_startup(engine)" in content


def test_database_scripts_do_not_echo_connection_secrets():
    combined = read(BACKUP) + read(RESTORE)

    assert "set -x" not in combined
    assert "echo $PGPASSWORD" not in combined
    assert "echo $DATABASE_URL" not in combined
    assert "echo $RESTORE_DATABASE_URL" not in combined


def test_backup_artifacts_are_excluded_from_git_and_container():
    for path in (GITIGNORE, DOCKERIGNORE):
        content = read(path)
        assert "*.dump" in content
        assert "*.backup" in content
        assert "backups/" in content
