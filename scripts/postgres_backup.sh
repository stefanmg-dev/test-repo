#!/bin/sh
set -eu

: "${PGHOST:?PGHOST is required}"
: "${PGDATABASE:?PGDATABASE is required}"
: "${PGUSER:?PGUSER is required}"
: "${BACKUP_FILE:?BACKUP_FILE is required}"

case "$BACKUP_FILE" in
    *.dump) ;;
    *)
        echo "BACKUP_FILE must end with .dump" >&2
        exit 2
        ;;
esac

if [ -e "$BACKUP_FILE" ]; then
    echo "Backup destination already exists" >&2
    exit 2
fi

backup_dir=$(dirname "$BACKUP_FILE")
if [ ! -d "$backup_dir" ]; then
    echo "Backup destination directory does not exist" >&2
    exit 2
fi

umask 077
pg_dump \
    --format=custom \
    --file="$BACKUP_FILE" \
    --no-owner \
    --no-privileges \
    --host="$PGHOST" \
    --port="${PGPORT:-5432}" \
    --username="$PGUSER" \
    "$PGDATABASE"

pg_restore --list "$BACKUP_FILE" >/dev/null

echo "PostgreSQL backup completed and archive verified"
