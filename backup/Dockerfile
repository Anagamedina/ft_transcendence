FROM alpine:3.21

# The backup worker only needs the PostgreSQL client tools. Using the server
# image declares PGDATA as a Docker VOLUME and creates an unused anonymous
# volume every time this container is recreated.
RUN apk add --no-cache postgresql16-client gzip

COPY backup.sh run.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/run.sh

# pg_dump does not need root. This user can only write to /backups.
RUN adduser -D -H -u 10002 -s /sbin/nologin backup \
    && mkdir -p /backups \
    && chown backup:backup /backups
USER backup

ENTRYPOINT ["run.sh"]
