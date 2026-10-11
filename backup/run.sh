#!/bin/sh

echo "backup: one backup every ${BACKUP_INTERVAL_HOURS}h, keeping the last ${BACKUP_KEEP}"

# Checks once a minute whether the newest backup is older than the interval.
# Restarting the container does not create an extra backup.
while true; do
	recent="$(find /backups -name 'aquaguard-*.sql.gz' -mmin "-$((BACKUP_INTERVAL_HOURS * 60))")"
	if [ -z "$recent" ]; then
		backup.sh
	fi
	sleep 60
done
