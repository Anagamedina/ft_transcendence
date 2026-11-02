#!/bin/sh

cd "$(dirname "$0")/.."
. ./.env

SENSOR_ID=00000000-0000-4000-8000-000000000001

fail() {
	echo "smoke: FAIL  $1"
	exit 1
}

ok() {
	echo "smoke: ok    $1"
}

sql() {
	docker compose exec -T database psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "$1"
}

echo "smoke: waiting up to 60s for database, backend and gateway..."
docker compose up -d --wait --wait-timeout 60 database backend gateway \
	|| fail "the stack is not healthy. Check it with: docker compose ps"
ok "database, backend and gateway are healthy"

curl -skf https://localhost/api/health > /dev/null \
	|| fail "/api/health does not respond. Check: docker compose logs backend"
ok "/api/health responds"

curl -skf https://localhost/api/health/db > /dev/null \
	|| fail "/api/health/db does not respond. Check: docker compose logs backend database"
ok "/api/health/db responds"

curl -skf https://localhost/api/status | grep -q '"name":"backup"' \
	|| fail "/api/status does not respond. Check: docker compose logs backend"
ok "/api/status responds"

curl -sI http://localhost/ | grep -q "301" \
	|| fail "HTTP does not redirect to HTTPS. Check: docker compose logs gateway"
ok "HTTP redirects to HTTPS"

curl -skf https://localhost/ | grep -q '<div id="app">' \
	|| fail "the gateway does not serve the SPA. Check: docker compose logs gateway"
ok "the gateway serves the SPA"

[ "$(sql "SELECT count(*) FROM sensors WHERE id = '$SENSOR_ID'")" = "1" ] \
	|| fail "the demo sensor does not exist. Load the demo data with: make seed"

READING_ID="$(cat /proc/sys/kernel/random/uuid)"

curl -skf -X POST https://localhost/api/readings \
	-H "Content-Type: application/json" \
	-H "X-Ingest-Key: ${INGEST_API_KEY:-dev-only-ingest-key}" \
	-d "{\"id\": \"$READING_ID\", \"sensor_id\": \"$SENSOR_ID\", \"pressure\": 3.5}" > /dev/null \
	|| fail "POST /api/readings failed. Check: docker compose logs backend"
ok "POST /api/readings accepts a reading"

[ "$(sql "SELECT count(*) FROM readings WHERE id = '$READING_ID'")" = "1" ] \
	|| fail "the reading was not stored in PostgreSQL"
ok "the reading is stored in PostgreSQL"

sql "DELETE FROM readings WHERE id = '$READING_ID'" > /dev/null

if [ -z "$(docker compose ps -q simulator)" ]; then
	echo "smoke: skip  simulator is not running (make sim)"
elif [ "$SIMULATOR_SCENARIO" = "offline" ]; then
	echo "smoke: skip  simulator scenario is offline, it sends no readings on purpose"
else
	recent="$(sql "SELECT count(*) FROM readings WHERE created_at > now() - interval '30 seconds'")"
	[ "$recent" -gt 0 ] \
		|| fail "no simulator readings in the last 30s. Check: docker compose logs simulator"
	ok "simulator readings reach the database ($recent in the last 30s)"
fi

echo "smoke: OK, all checks passed"
