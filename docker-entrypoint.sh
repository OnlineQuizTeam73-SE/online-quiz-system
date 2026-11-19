#!/bin/sh
set -eu

db_path="${DATABASE_PATH:-/data/quiz.db}"
db_dir="$(dirname "$db_path")"
mkdir -p "$db_dir"

# schema.sql uses CREATE TABLE IF NOT EXISTS. Applying it at startup creates a
# fresh database or adds missing tables without deleting or resetting any data.
DATABASE_PATH="$db_path" python - <<'PY'
import os
import sqlite3

database_path = os.environ["DATABASE_PATH"]
schema_path = "/app/schema.sql"

connection = sqlite3.connect(database_path)
try:
    with open(schema_path, encoding="utf-8") as schema_file:
        connection.executescript(schema_file.read())
    connection.commit()
finally:
    connection.close()
PY

exec gunicorn \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${GUNICORN_WORKERS:-2}" \
    --access-logfile - \
    --error-logfile - \
    app:app
