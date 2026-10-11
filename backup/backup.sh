#!/bin/sh

FILE="/backups/aquaguard-$(date -u +%Y%m%d-%H%M%S).sql.gz"

# The dump goes to a temporary name and is renamed only when it finishes, so
# every aquaguard-*.sql.gz in the volume is a complete backup.
if ! pg_dump --clean --if-exists --compress=6 --file="$FILE.tmp"; then
	rm -f "$FILE.tmp"
	echo "backup: FAIL  pg_dump did not finish"
	exit 1
fi
mv "$FILE.tmp" "$FILE"
echo "backup: ok    $FILE ($(du -h "$FILE" | cut -f1))"

ls -1 /backups/aquaguard-*.sql.gz | sort -r | tail -n +"$((BACKUP_KEEP + 1))" | xargs -r rm -f
