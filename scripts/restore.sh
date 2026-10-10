#!/bin/sh

cd "$(dirname "$0")/.."
. ./.env

FILE="$1"

fail() {
	echo "restore: FAIL  $1"
	exit 1
}

[ -n "$FILE" ] || fail "no backup given. Usage: make restore FILE=<name>  (list them with: make backups)"

docker compose exec -T backup test -f "/backups/$FILE" \
	|| fail "/backups/$FILE does not exist. List the backups with: make backups"

SIMULATOR="$(docker compose ps -q simulator)"

echo "restore: stopping backend and simulator so nothing writes during the restore..."
docker compose --profile sim stop backend simulator

# The dump was made with --clean, so it drops every table and creates it again
# with the saved data. In a single transaction, a failure leaves the database
# exactly as it was.
echo "restore: loading $FILE..."
docker compose exec -T backup sh -c "gunzip -c '/backups/$FILE' | psql --quiet --single-transaction -v ON_ERROR_STOP=1" > /dev/null \
	|| fail "psql could not load the backup. The database was left untouched. Start the backend again with: make up"

echo "restore: starting the backend again..."
docker compose up -d --wait backend gateway \
	|| fail "the backend is not healthy after the restore. Check: docker compose logs backend"

if [ -n "$SIMULATOR" ]; then
	docker compose --profile sim up -d simulator
fi

echo "restore: OK, $FILE restored. Check it with: make smoke"
