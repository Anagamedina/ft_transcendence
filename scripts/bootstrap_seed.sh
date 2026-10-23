#!/bin/sh

set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT"

fail() {
  echo "bootstrap: FAIL  $1" >&2
  exit 1
}

# shellcheck disable=SC1091
. ./.env

# The demo users have public passwords, and seed_demo.py refuses to run in
# production. An empty production database starts empty instead of failing.
if [ "${ENV-}" = "production" ]; then
  echo "bootstrap: ENV=production; skipping the demo seed"
  exit 0
fi

# "Empty" means no organizations and no users. Counting only organizations
# would load the demo users again over real accounts left without one.
count="$(docker compose exec -T database \
  psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  'SELECT (SELECT count(*) FROM organizations) + (SELECT count(*) FROM users)')" \
  || fail "could not query the database; is it running and migrated?"

case "$count" in
  '' | *[!0-9]*)
    fail "could not determine whether the database is empty"
    ;;
  0)
    echo "bootstrap: database is empty; loading the demo seed"
    make seed
    ;;
  *)
    echo "bootstrap: database already contains $count organization(s) and user(s); preserving existing data"
    ;;
esac
