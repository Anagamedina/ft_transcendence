# DOCKERFILE BACKEND
# Instalar deps → alembic upgrade → uvicorn app.main:app en :8000 (red interna).
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]