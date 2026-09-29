# PostgreSQL backup and restore runbook

## Scope

This runbook defines a logical backup and verification workflow for the application PostgreSQL database. It uses a custom-format `pg_dump` archive and restores only into a separate empty verification database. It does not replace provider snapshots, physical backups, WAL archiving, or a point-in-time recovery plan.

## Security rules

- Supply connection values through environment variables or the deployment secret mechanism.
- Never put database passwords in command arguments, committed files, shell history, logs, or backup filenames.
- Store archives outside the repository with restricted filesystem permissions.
- Treat every archive as sensitive because processing runs can contain extracted and reviewed document values.
- Restore only archives produced by a trusted source. PostgreSQL restores can execute code contained in the archive.
- Never use the restore script against the production database.

## Required client tools

The operator environment requires compatible `pg_dump`, `pg_restore`, and `psql` clients. Verify them before starting:

```bash
pg_dump --version
pg_restore --version
psql --version
```

## Create and verify a backup

Set the standard PostgreSQL client variables through a secure mechanism. `PGPASSWORD` may be supplied by the secret mechanism or replaced with a protected `.pgpass` file.

```bash
export PGHOST="database-host"
export PGPORT="5432"
export PGDATABASE="document_processing"
export PGUSER="backup-role"
export PGPASSWORD="provided-by-secret-mechanism"
export BACKUP_FILE="/secure/backups/document-processing-YYYYMMDDTHHMMSSZ.dump"

./scripts/postgres_backup.sh
```

The script:

1. requires an explicit `.dump` destination;
2. refuses to overwrite an existing file;
3. creates the archive with restrictive process permissions;
4. excludes source ownership and privilege commands;
5. verifies that `pg_restore` can read the archive catalog;
6. does not print connection values or credentials.

A successful command only proves that an archive was created and its catalog is readable. Recovery readiness requires a full restore verification.

## Prepare a restore verification database

Create a new empty database using infrastructure tooling or an authorized administration account. Its name must end with `_restore` or `_test`, for example `document_processing_restore`.

Use a dedicated verification environment. Do not point application traffic at it. The restore role needs sufficient permissions to create the archived schema objects in that database.

## Restore and verify

Set destination-specific PostgreSQL variables. Keep source `PGHOST` and `PGDATABASE` set when possible so the guard can also reject an identical source and destination pair.

`RESTORE_DATABASE_URL` is the SQLAlchemy URL used only by the application startup validator after `pg_restore` completes.

```bash
export RESTORE_PGHOST="verification-database-host"
export RESTORE_PGPORT="5432"
export RESTORE_PGDATABASE="document_processing_restore"
export RESTORE_PGUSER="restore-role"
export PGPASSWORD="provided-by-secret-mechanism"
export RESTORE_DATABASE_URL="postgresql+psycopg://restore-role:secret@verification-database-host:5432/document_processing_restore"
export BACKUP_FILE="/secure/backups/document-processing-YYYYMMDDTHHMMSSZ.dump"
export RESTORE_CONFIRM="RESTORE"

./scripts/postgres_restore_verify.sh
```

The script refuses to continue unless:

- the confirmation is exactly `RESTORE`;
- the destination name ends with `_restore` or `_test`;
- the source and destination pair are not identical when source variables are present;
- the archive exists and its catalog is readable;
- the destination public schema contains no application objects.

After restore, the script runs the existing application startup validation against the destination database. The verification succeeds only when PostgreSQL is reachable and the restored Alembic revision equals the repository head.

## Application-level verification

After the script succeeds, start one isolated application instance against the restored database and verify:

1. `GET /ready` returns ready, connected, and current migration status.
2. Processing History can list and open representative runs.
3. Review metadata, collections, configuration identity, and Universal Invoice shadow metadata are present where expected.
4. Tenant-scoped principals cannot read runs owned by another tenant.
5. No production traffic, retention execution, or configuration writes target the verification database.

Do not use document values in screenshots, tickets, or routine restore logs.

## Failure handling

- If archive verification fails, discard the archive and investigate the backup job.
- If the destination is not empty, create a new empty destination instead of using a destructive clean restore.
- If Alembic parity fails, preserve the verification database for investigation and do not report the backup as recovery-ready.
- If the archive source is not trusted, do not restore it.
- Remove or securely expire verification databases and archives according to the approved retention and incident-response policy.

## Automation gate

Do not schedule automated retention solely because backup creation succeeds. First demonstrate a complete restore, application startup validation, representative data checks, tenant-isolation checks, and documented ownership for recurring recovery tests.
