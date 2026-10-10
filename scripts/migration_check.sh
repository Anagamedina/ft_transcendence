#!/bin/sh
set -u

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

run_alembic() {
	result="$(docker compose --project-directory "$ROOT" run --rm --no-deps \
		-v "$ROOT/backend/app:/app/app:ro" \
		-v "$ROOT/backend/migrations:/app/migrations:ro" \
		--entrypoint alembic backend "$@" 2>&1)"
	status=$?
	printf '%s\n' "$result" | grep -v -e "INFO  \[alembic" -e "ERROR \[alembic"
	return $status
}

if ! output="$(run_alembic current)"; then
	if printf '%s' "$output" | grep -q "OperationalError"; then
		echo "migration-check: cannot connect to the database. Is the stack running? (make up)"
	else
		echo "migration-check: cannot read the database revision."
		echo "$output"
	fi
	exit 1
fi
current="$output"

if ! run_alembic current --check-heads >/dev/null; then
	heads="$(run_alembic heads)"
	echo "migration-check: pending migrations, the database is not at head."
	echo "  current: ${current:-<empty database>}"
	echo "  head:    $heads"
	echo "Apply them with: make migrate"
	exit 1
fi

if ! output="$(run_alembic check)"; then
	echo "migration-check: models and migrations are out of sync (drift)."
	echo "$output"
	echo "Create a migration with: make migration MSG=\"description\""
	exit 1
fi

echo "migration-check: OK, database at head ($current) and no drift."
