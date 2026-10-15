FROM alpine:3.21

# The backup worker only needs the PostgreSQL client tools. Using the server
# image declares PGDATA as a Docker VOLUME and creates an unused anonymous
# volume every time this container is recreated.
RUN apk add --no-cache postgresql16-client gzip

COPY backup.sh run.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/run.sh

ENTRYPOINT ["run.sh"]
