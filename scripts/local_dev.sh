#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_FILE="/tmp/ai-code-assistant-uvicorn.pid"
DEFAULT_DATABASE_URL="postgresql+psycopg:///document_processing?host=/tmp"
export DATABASE_URL="${DATABASE_URL:-$DEFAULT_DATABASE_URL}"
cd "$ROOT_DIR"

is_running() {
    [[ -f "$PID_FILE" ]] || return 1
    local pid
    pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    [[ "$pid" =~ ^[0-9]+$ ]] || return 1
    kill -0 "$pid" 2>/dev/null
}

cleanup_stale_pid() {
    if [[ -f "$PID_FILE" ]] && ! is_running; then
        rm -f "$PID_FILE"
    fi
}

check_database() {
    if ! pg_isready >/dev/null 2>&1; then
        echo "PostgreSQL is not accepting connections."
        echo "Start it with: brew services start postgresql@17"
        return 1
    fi
}

start_server() {
    cleanup_stale_pid
    if is_running; then
        echo "Local API is already running with PID $(cat "$PID_FILE")."
        return 0
    fi

    check_database
    echo "Applying pending local database migrations..."
    alembic upgrade head

    echo "Starting API at http://127.0.0.1:8000"
    echo "UI: http://127.0.0.1:8000/ui/test.html"
    echo "Press Ctrl+C to stop."

    uvicorn api:app --reload --host 127.0.0.1 --port 8000 &
    local server_pid=$!
    echo "$server_pid" > "$PID_FILE"

    cleanup() {
        if kill -0 "$server_pid" 2>/dev/null; then
            kill "$server_pid" 2>/dev/null || true
            wait "$server_pid" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    }

    trap cleanup EXIT INT TERM
    wait "$server_pid"
}

show_status() {
    cleanup_stale_pid

    echo "--- PROJECT ---"
    git log -1 --oneline
    git status --short

    echo
    echo "--- PYTHON ---"
    command -v python
    python --version

    echo
    echo "--- DATABASE ---"
    echo "DATABASE_URL=$DATABASE_URL"
    pg_isready || true
    if pg_isready >/dev/null 2>&1; then
        alembic current
    fi

    echo
    echo "--- API ---"
    if is_running; then
        echo "PID $(cat "$PID_FILE") is running."
    else
        echo "No API process recorded by the local helper."
    fi

    local health_response
    local ready_response

    if health_response="$(
        curl -fsS --max-time 2             http://127.0.0.1:8000/health             2>/dev/null
    )"; then
        echo "$health_response"

        if ready_response="$(
            curl -fsS --max-time 2                 http://127.0.0.1:8000/ready                 2>/dev/null
        )"; then
            echo "$ready_response"
        else
            echo "API is reachable, but readiness check failed."
        fi
    else
        echo "API is not reachable on 127.0.0.1:8000."
    fi
}

stop_server() {
    cleanup_stale_pid
    if ! is_running; then
        echo "No API process recorded by the local helper."
        return 0
    fi

    local pid
    pid="$(cat "$PID_FILE")"
    kill "$pid"

    for _ in 1 2 3 4 5; do
        if ! kill -0 "$pid" 2>/dev/null; then
            rm -f "$PID_FILE"
            echo "Local API stopped."
            return 0
        fi
        sleep 1
    done

    echo "API process $pid did not stop within 5 seconds."
    return 1
}

show_help() {
    cat <<'EOF'
Usage: bash scripts/local_dev.sh <command>

Commands:
  start   Check PostgreSQL, apply migrations, and run Uvicorn in foreground
  status  Show Git, Python, database, migration, and API health status
  stop    Stop an API started by this helper
  check   Check PostgreSQL and Alembic without starting the API
EOF
}

case "${1:-}" in
    start)
        start_server
        ;;
    status)
        show_status
        ;;
    stop)
        stop_server
        ;;
    check)
        check_database
        alembic current
        alembic check
        ;;
    *)
        show_help
        exit 2
        ;;
esac
