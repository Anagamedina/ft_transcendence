# DOCKERFILE BACKEND
# Instalar deps → alembic upgrade → uvicorn app.main:app en :8000 (red interna).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY migrations ./migrations
COPY alembic.ini .

COPY tools/entrypoint.sh ./tools/entrypoint.sh
RUN chmod +x tools/entrypoint.sh

ENTRYPOINT ["sh", "./tools/entrypoint.sh"]