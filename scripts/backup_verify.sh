#!/bin/bash
#
# Checks that a backup can be restored, using a temporary database.
# The real database is only read, never changed.
#
#   make backup-verify              new backup, compared with the real database
#   make backup-verify FILE=<name>  existing backup, rows shown but not compared
#
# Steps:
#   1. Check that the containers are running
#   2. Read the tables of the real database
#   3. Pause the simulator and make a new backup (or use FILE)
#   4. Check that the .gz file is complete
#   5. Load the backup into the temporary database
#   6. Check that the backup has every table
#   7. Compare the rows of every table and the Alembic version
#   At the end, always: drop the temporary database and resume the simulator


# The name of the backup to check. It is empty when FILE is not given.
FILE="$1"

TEMP_DB="aquaguard_restore_check"

# "yes" when we make a new backup, "no" when we check an existing one.
if [ -z "$FILE" ]; then
	NEW_BACKUP="yes"
else
	NEW_BACKUP="no"
fi

# Remembers whether we paused the simulator, so we can start it again.
SIMULATOR_PAUSED="no"


# Prints an error and stops the script with exit code 1.
fail() {
	echo "backup-verify: FAIL  $1"
	exit 1
}

# Runs one SQL query on the real database and prints the result.
sql_real() {
	docker compose exec -T backup psql -X -A -t -c "$1"
}

# Runs one SQL query on the temporary database and prints the result.
sql_temp() {
	docker compose exec -T backup psql -X -A -t -d "$TEMP_DB" -c "$1"
}

# Runs when the script ends, whether it worked, failed or was stopped with
# Ctrl+C. It removes the temporary database and starts the simulator again.
clean_up() {
	docker compose exec -T backup dropdb --if-exists --force "$TEMP_DB" > /dev/null 2>&1
	if [ "$SIMULATOR_PAUSED" = "yes" ]; then
		docker compose unpause simulator > /dev/null 2>&1
		echo "backup-verify: simulator running again"
	fi
}
trap clean_up EXIT

# Ctrl+C stops the whole script (exit code 130). Without this line, when
# Ctrl+C arrives during a docker command, bash would go on with the next step.
trap "exit 130" INT


echo "backup-verify: [1/7] checking that the containers are running"

if [ -z "$(docker compose ps --status running -q database)" ]; then
	fail "database is not running. Start the stack with: make up"
fi
if [ -z "$(docker compose ps --status running -q backup)" ]; then
	fail "backup is not running. Start the stack with: make up"
fi


echo "backup-verify: [2/7] reading the tables of the real database"

TABLES="$(sql_real "SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename")"

if [ -z "$TABLES" ]; then
	fail "the real database has no tables. Run: make migrate"
fi


if [ "$NEW_BACKUP" = "yes" ]; then
	echo "backup-verify: [3/7] making a new backup"

	# The simulator writes new readings every few seconds. We pause it, so
	# the real database does not change while we compare it with the backup.
	if [ -n "$(docker compose ps --status running -q simulator)" ]; then
		docker compose pause simulator > /dev/null 2>&1
		SIMULATOR_PAUSED="yes"
		echo "backup-verify: simulator paused during the check"
		# Give the last reading it sent time to be saved.
		sleep 1
	fi

	# backup.sh is the same script that `make backup` and the backup
	# service use. It saves a new aquaguard-<date>.sql.gz in /backups.
	if ! docker compose exec -T backup backup.sh > /dev/null; then
		fail "pg_dump did not finish. Check: docker compose logs backup"
	fi

	# The new backup is the most recent file in /backups.
	FILE="$(docker compose exec -T backup sh -c 'ls /backups/aquaguard-*.sql.gz | sort | tail -n 1')"
else
	echo "backup-verify: [3/7] using the existing backup $FILE"
fi

# Keep only the file name: "/backups/aquaguard-X.sql.gz" -> "aquaguard-X.sql.gz"
FILE="$(basename "$FILE")"

if ! docker compose exec -T backup test -f "/backups/$FILE"; then
	fail "/backups/$FILE does not exist. List the backups with: make backups"
fi


echo "backup-verify: [4/7] checking that $FILE is a complete gzip file"

# gunzip -t reads the whole file without unpacking it. It fails if the file
# is cut in the middle or damaged.
if ! docker compose exec -T backup gunzip -t "/backups/$FILE" 2> /dev/null; then
	fail "$FILE is not a valid gzip file: it is truncated or damaged"
fi


echo "backup-verify: [5/7] loading $FILE into the temporary database $TEMP_DB"

# Remove a temporary database left by an earlier run, then create it empty.
docker compose exec -T backup dropdb --if-exists --force "$TEMP_DB" > /dev/null 2>&1
if ! docker compose exec -T backup createdb "$TEMP_DB"; then
	fail "cannot create the temporary database $TEMP_DB"
fi

# Same command as `make restore` (scripts/restore.sh), but with -d TEMP_DB so
# it goes into the temporary database instead of the real one.
if ! docker compose exec -T backup sh -c "gunzip -c /backups/$FILE | psql -X --quiet --single-transaction -v ON_ERROR_STOP=1 -d $TEMP_DB" > /dev/null 2>&1; then
	fail "psql could not load $FILE: the SQL inside is damaged"
fi


echo "backup-verify: [6/7] checking that the backup has every table"

# A backup made before the migrations loads without errors, but is empty.
MISSING_TABLES=""
for TABLE in $TABLES; do
	FOUND="$(sql_temp "SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename = '$TABLE'")"
	if [ "$FOUND" != "1" ]; then
		MISSING_TABLES="$MISSING_TABLES $TABLE"
	fi
done

if [ -n "$MISSING_TABLES" ]; then
	fail "tables missing in the backup:$MISSING_TABLES"
fi


echo "backup-verify: [7/7] counting the rows of every table"
echo

# Print a table: one line per database table, with its rows in the real
# database and in the backup.
ALL_ROWS_MATCH="yes"
printf '%-16s %10s %10s\n' "table" "real" "backup"

for TABLE in $TABLES; do
	ROWS_REAL="$(sql_real "SELECT count(*) FROM \"$TABLE\"")"
	ROWS_BACKUP="$(sql_temp "SELECT count(*) FROM \"$TABLE\"")"

	if [ "$ROWS_REAL" = "$ROWS_BACKUP" ]; then
		printf '%-16s %10s %10s\n' "$TABLE" "$ROWS_REAL" "$ROWS_BACKUP"
	else
		printf '%-16s %10s %10s  <-- different\n' "$TABLE" "$ROWS_REAL" "$ROWS_BACKUP"
		ALL_ROWS_MATCH="no"
	fi
done

# Alembic writes the version of the database schema in this table.
VERSION_REAL="$(sql_real "SELECT version_num FROM alembic_version")"
VERSION_BACKUP="$(sql_temp "SELECT version_num FROM alembic_version")"

echo
echo "alembic version: real $VERSION_REAL, backup $VERSION_BACKUP"
echo


if [ "$NEW_BACKUP" = "yes" ]; then
	# A new backup: it must be exactly like the real database.
	if [ "$ALL_ROWS_MATCH" = "no" ]; then
		fail "the restored rows do not match the real database"
	fi
	if [ "$VERSION_REAL" != "$VERSION_BACKUP" ]; then
		fail "alembic version $VERSION_BACKUP in the backup, $VERSION_REAL in the real database"
	fi
	echo "backup-verify: OK, $FILE can be restored"
else
	# An older backup: different rows are normal, so they are not an error.
	if [ -z "$VERSION_BACKUP" ]; then
		fail "the backup has no alembic version"
	fi
	if [ "$VERSION_REAL" != "$VERSION_BACKUP" ]; then
		# Not an error either: when the backend starts after `make restore`,
		# it applies the migrations that are missing.
		echo "backup-verify: note  the backup has an older alembic version; make restore updates it when the backend starts"
	fi
	echo "backup-verify: OK, $FILE can be restored (rows not compared: it is an older backup)"
fi
