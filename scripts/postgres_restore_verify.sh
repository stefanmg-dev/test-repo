#!/bin/sh
set -eu

: "${RESTORE_PGHOST:?RESTORE_PGHOST is required}"
: "${RESTORE_PGDATABASE:?RESTORE_PGDATABASE is required}"
: "${RESTORE_PGUSER:?RESTORE_PGUSER is required}"
: "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"
: "${RESTORE_CONFIRM:?RESTORE_CONFIRM is required}"

if [ "$RESTORE_CONFIRM" != "RESTORE" ]; then
    echo "RESTORE_CONFIRM must be exactly RESTORE" >&2
    exit 2
fi

case "$RESTORE_PGDATABASE" in
    *_restore|*_test) ;;
    *)
        echo "Restore database name must end with _restore or _test" >&2
        exit 2
        ;;
esac

if [ "${PGHOST:-}" = "$RESTORE_PGHOST" ] && \
   [ "${PGDATABASE:-}" = "$RESTORE_PGDATABASE" ]; then
    echo "Source and restore databases must be different" >&2
    exit 2
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup archive does not exist" >&2
    exit 2
fi

pg_restore --list "$BACKUP_FILE" >/dev/null

object_count=$(psql \
    --no-psqlrc \
    --tuples-only \
    --no-align \
    --host="$RESTORE_PGHOST" \
    --port="${RESTORE_PGPORT:-5432}" \
    --username="$RESTORE_PGUSER" \
    --dbname="$RESTORE_PGDATABASE" \
    --command="SELECT count(*) FROM pg_class WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r','p','v','m','S','f');")

if [ "$object_count" != "0" ]; then
    echo "Restore destination must be an empty database" >&2
    exit 2
fi

pg_restore \
    --exit-on-error \
    --no-owner \
    --no-privileges \
    --host="$RESTORE_PGHOST" \
    --port="${RESTORE_PGPORT:-5432}" \
    --username="$RESTORE_PGUSER" \
    --dbname="$RESTORE_PGDATABASE" \
    "$BACKUP_FILE"

DATABASE_URL="$RESTORE_DATABASE_URL" python - <<'PYTHON'
from database import engine
from startup_validation import validate_database_startup

result = validate_database_startup(engine)
assert result.database_connected is True
assert result.current_revisions == result.expected_revisions
print("Restored database connectivity and Alembic parity verified")
PYTHON
