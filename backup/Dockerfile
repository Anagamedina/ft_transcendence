FROM postgres:16-alpine

COPY backup.sh run.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/backup.sh /usr/local/bin/run.sh

ENTRYPOINT ["run.sh"]
