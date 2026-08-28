# MAIN — punto de entrada FastAPI
# Montar CORS, handlers de error, routers de modules/* bajo /api.
# Exponer GET /api/health y OpenAPI en /api/docs.
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

"""
FastAPI
  → Depends(get_db)
  → Session
  → Engine
  → PostgreSQL
  → SELECT 1
"""
app= FastAPI()

@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": result.scalar_one(),
    }