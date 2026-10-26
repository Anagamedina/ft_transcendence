# DOCKERFILE BACKEND
# Instalar deps → alembic upgrade → uvicorn app.main:app en :8000 (red interna).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY seeds ./seeds
COPY migrations ./migrations
COPY alembic.ini .

COPY tools/entrypoint.sh ./tools/entrypoint.sh
RUN chmod +x tools/entrypoint.sh

# Run as a normal user, not root. It can run the code but not change it,
# and it can only write to the documents folder.
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir -p /data/documents \
    && chown app:app /data/documents
USER app

# The filesystem is read-only, so Python must not write .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1

ENTRYPOINT ["sh", "./tools/entrypoint.sh"]
