#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
. ./.env

fail() {
  echo "storage-check: FAIL  $1" >&2
  exit 1
}

ok() {
  echo "storage-check: ok    $1"
}

mounts() {
  docker inspect --format '{{range .Mounts}}{{.Type}}|{{.Destination}}|{{.RW}}{{"\n"}}{{end}}' \
    "$(docker compose ps -q "$1")"
}

has_mount() {
  mounts "$1" | grep -qx "$2|$3|$4"
}

has_mount database volume /var/lib/postgresql/data true \
  || fail "postgres_data is not a writable named volume on database"
has_mount backend volume "${DOCUMENTS_DIR:-/data/documents}" true \
  || fail "documents_data is not a writable named volume on backend"
has_mount backend volume /backups false \
  || fail "backups_data must be read-only on backend"
has_mount backup volume /backups true \
  || fail "backups_data is not writable on backup"
mounts backup | grep -q '|/var/lib/postgresql/data|' \
  && fail "backup must not create a PGDATA mount"
ok "database, documents and backups have the expected mounts"

sql() {
  docker compose exec -T database \
    psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1"
}

[ "$(sql "SELECT count(*) FROM organizations")" -gt 0 ] \
  || fail "the database has no organizations after bootstrap"
[ "$(sql "SELECT count(*) FROM sensors WHERE id = '00000000-0000-4000-8000-000000000001'")" = "1" ] \
  || fail "the demo sensor is missing"
[ "$(sql "SELECT count(*) FROM readings")" -gt 0 ] \
  || fail "the database has no readings after bootstrap"
ok "seed data is stored in PostgreSQL"

docker compose exec -T backend sh -c 'test -d "${DOCUMENTS_DIR:-/data/documents}" && test -w "${DOCUMENTS_DIR:-/data/documents}"' \
  || fail "the backend cannot access DOCUMENTS_DIR"
ok "documents directory is available to backend"

docker compose exec -T backup sh -c '
  latest=$(ls -t /backups/aquaguard-*.sql.gz 2>/dev/null | head -n 1) || exit 1
  test -n "$latest" && gzip -t "$latest"
' || fail "no valid compressed backup exists"
ok "a valid backup is stored in backups_data"
