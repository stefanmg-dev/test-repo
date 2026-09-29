import os
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKUP_SCRIPT = PROJECT_ROOT / "scripts" / "postgres_backup.sh"
RESTORE_SCRIPT = PROJECT_ROOT / "scripts" / "postgres_restore_verify.sh"


def write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


def run_script(script: Path, env: dict[str, str]):
    return subprocess.run(
        ["sh", str(script)],
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def base_env(stub_dir: Path, log_file: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{stub_dir}:{env['PATH']}",
            "COMMAND_LOG": str(log_file),
            "PGPASSWORD": "source-secret-value",
        }
    )
    return env


def install_backup_stubs(stub_dir: Path) -> None:
    write_executable(
        stub_dir / "pg_dump",
        '''#!/bin/sh
set -eu
printf 'pg_dump' >> "$COMMAND_LOG"
for argument in "$@"; do
    printf ' <%s>' "$argument" >> "$COMMAND_LOG"
done
printf '\\n' >> "$COMMAND_LOG"
output=""
for argument in "$@"; do
    case "$argument" in
        --file=*) output=${argument#--file=} ;;
    esac
done
: "${output:?missing output}"
printf 'stub archive' > "$output"
''',
    )
    write_executable(
        stub_dir / "pg_restore",
        '''#!/bin/sh
set -eu
printf 'pg_restore' >> "$COMMAND_LOG"
for argument in "$@"; do
    printf ' <%s>' "$argument" >> "$COMMAND_LOG"
done
printf '\\n' >> "$COMMAND_LOG"
''',
    )


def install_restore_stubs(
    stub_dir: Path,
    *,
    object_count: str = "0",
) -> None:
    write_executable(
        stub_dir / "pg_restore",
        '''#!/bin/sh
set -eu
printf 'pg_restore' >> "$COMMAND_LOG"
for argument in "$@"; do
    printf ' <%s>' "$argument" >> "$COMMAND_LOG"
done
printf '\\n' >> "$COMMAND_LOG"
''',
    )
    write_executable(
        stub_dir / "psql",
        f'''#!/bin/sh
set -eu
printf 'psql' >> "$COMMAND_LOG"
for argument in "$@"; do
    printf ' <%s>' "$argument" >> "$COMMAND_LOG"
done
printf '\\n' >> "$COMMAND_LOG"
printf '{object_count}\\n'
''',
    )
    write_executable(
        stub_dir / "python",
        '''#!/bin/sh
set -eu
printf 'python' >> "$COMMAND_LOG"
for argument in "$@"; do
    printf ' <%s>' "$argument" >> "$COMMAND_LOG"
done
printf '\\n' >> "$COMMAND_LOG"
cat >/dev/null
''',
    )


def test_backup_refuses_existing_destination_before_running_commands(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_backup_stubs(stub_dir)
    backup_file = tmp_path / "existing.dump"
    backup_file.write_bytes(b"existing")
    env = base_env(stub_dir, log_file)
    env.update(
        {
            "PGHOST": "source-db",
            "PGDATABASE": "document_processing",
            "PGUSER": "backup-role",
            "BACKUP_FILE": str(backup_file),
        }
    )

    result = run_script(BACKUP_SCRIPT, env)

    assert result.returncode == 2
    assert "Backup destination already exists" in result.stderr
    assert not log_file.exists()
    assert "source-secret-value" not in result.stdout + result.stderr


def test_backup_invokes_custom_dump_and_archive_validation(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_backup_stubs(stub_dir)
    backup_file = tmp_path / "fresh.dump"
    env = base_env(stub_dir, log_file)
    env.update(
        {
            "PGHOST": "source-db",
            "PGPORT": "5433",
            "PGDATABASE": "document_processing",
            "PGUSER": "backup-role",
            "BACKUP_FILE": str(backup_file),
        }
    )

    result = run_script(BACKUP_SCRIPT, env)

    assert result.returncode == 0, result.stderr
    assert backup_file.read_bytes() == b"stub archive"
    commands = log_file.read_text(encoding="utf-8")
    assert "pg_dump <--format=custom>" in commands
    assert f"<--file={backup_file}>" in commands
    assert "<--no-owner>" in commands
    assert "<--no-privileges>" in commands
    assert "<--host=source-db>" in commands
    assert "<--port=5433>" in commands
    assert "<--username=backup-role>" in commands
    assert "<document_processing>" in commands
    assert f"pg_restore <--list> <{backup_file}>" in commands
    assert "source-secret-value" not in commands
    assert "source-secret-value" not in result.stdout + result.stderr


def restore_env(
    stub_dir: Path,
    log_file: Path,
    backup_file: Path,
) -> dict[str, str]:
    env = base_env(stub_dir, log_file)
    env.update(
        {
            "PGHOST": "source-db",
            "PGDATABASE": "document_processing",
            "RESTORE_PGHOST": "restore-db",
            "RESTORE_PGPORT": "5440",
            "RESTORE_PGDATABASE": "document_processing_restore",
            "RESTORE_PGUSER": "restore-role",
            "RESTORE_DATABASE_URL": (
                "postgresql+psycopg://restore-role:"
                "restore-secret-value@restore-db:5440/"
                "document_processing_restore"
            ),
            "BACKUP_FILE": str(backup_file),
        }
    )
    return env


def test_restore_refuses_wrong_confirmation_before_commands(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_restore_stubs(stub_dir)
    backup_file = tmp_path / "trusted.dump"
    backup_file.write_bytes(b"archive")
    env = restore_env(stub_dir, log_file, backup_file)
    env["RESTORE_CONFIRM"] = "restore"

    result = run_script(RESTORE_SCRIPT, env)

    assert result.returncode == 2
    assert "RESTORE_CONFIRM must be exactly RESTORE" in result.stderr
    assert not log_file.exists()


def test_restore_refuses_unsafe_database_name_before_commands(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_restore_stubs(stub_dir)
    backup_file = tmp_path / "trusted.dump"
    backup_file.write_bytes(b"archive")
    env = restore_env(stub_dir, log_file, backup_file)
    env.update(
        {
            "RESTORE_CONFIRM": "RESTORE",
            "RESTORE_PGDATABASE": "document_processing",
        }
    )

    result = run_script(RESTORE_SCRIPT, env)

    assert result.returncode == 2
    assert "must end with _restore or _test" in result.stderr
    assert not log_file.exists()


def test_restore_refuses_non_empty_destination_before_restore(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_restore_stubs(stub_dir, object_count="3")
    backup_file = tmp_path / "trusted.dump"
    backup_file.write_bytes(b"archive")
    env = restore_env(stub_dir, log_file, backup_file)
    env["RESTORE_CONFIRM"] = "RESTORE"

    result = run_script(RESTORE_SCRIPT, env)

    assert result.returncode == 2
    assert "Restore destination must be an empty database" in result.stderr
    commands = log_file.read_text(encoding="utf-8")
    assert commands.count("pg_restore") == 1
    assert "pg_restore <--list>" in commands
    assert "psql" in commands
    assert "<--dbname=document_processing_restore>" in commands
    assert "python" not in commands


def test_restore_invokes_restore_and_application_validation(tmp_path):
    stub_dir = tmp_path / "bin"
    stub_dir.mkdir()
    log_file = tmp_path / "commands.log"
    install_restore_stubs(stub_dir, object_count="0")
    backup_file = tmp_path / "trusted.dump"
    backup_file.write_bytes(b"archive")
    env = restore_env(stub_dir, log_file, backup_file)
    env["RESTORE_CONFIRM"] = "RESTORE"

    result = run_script(RESTORE_SCRIPT, env)

    assert result.returncode == 0, result.stderr
    commands = log_file.read_text(encoding="utf-8")
    assert f"pg_restore <--list> <{backup_file}>" in commands
    assert "pg_restore <--exit-on-error>" in commands
    assert "<--no-owner>" in commands
    assert "<--no-privileges>" in commands
    assert "<--host=restore-db>" in commands
    assert "<--port=5440>" in commands
    assert "<--username=restore-role>" in commands
    assert "<--dbname=document_processing_restore>" in commands
    assert f"<{backup_file}>" in commands
    assert "python <->" in commands
    output = result.stdout + result.stderr + commands
    assert "source-secret-value" not in output
    assert "restore-secret-value" not in output
