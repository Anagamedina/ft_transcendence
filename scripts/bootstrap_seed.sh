#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

# shellcheck disable=SC1091
. ./.env

count="$(docker compose exec -T database \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc 'SELECT count(*) FROM organizations')"

case "$count" in
  '' | *[!0-9]*)
    echo "bootstrap: FAIL  could not determine whether the database is empty" >&2
    exit 1
    ;;
  0)
    echo "bootstrap: database is empty; loading the demo seed"
    make seed
    ;;
  *)
    echo "bootstrap: database already contains $count organization(s); preserving existing data"
    ;;
esac
