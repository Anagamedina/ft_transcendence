# Flujo: request → dependencia get_db → service/repository → commit/rollback.
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from app.core.config import settings

# ---------------------------------------------------------
# ENGINE
# ---------------------------------------------------------

# El Engine representa la infraestructura de conexión
# entre SQLAlchemy y PostgreSQL.
#
# Usa la DATABASE_URL construida en config.py:
#
# postgresql+psycopg://user:password@database:5432/aquaguard
#
# El Engine:
# - conoce dónde está PostgreSQL;
# - utiliza psycopg como driver;
# - administra un pool de conexiones;
# - será compartido por toda la aplicación.

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# ---------------------------------------------------------
# SESSION FACTORY
# ---------------------------------------------------------

# SessionLocal NO es una sesión.
#
# Es una fábrica que crea sesiones nuevas cuando
# la aplicación las necesita.
#
# SessionLocal()
#       ↓
# Session concreta
#
# Cada request podrá obtener su propia Session.

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------
# FASTAPI DATABASE DEPENDENCY
# ---------------------------------------------------------
"""
Crea una Session para una operación/request.

Flujo:

    SessionLocal()
          ↓
       Session
          ↓
        yield
          ↓
    FastAPI / Repository
          ↓
        close()

El bloque finally garantiza que la sesión se cierre
incluso si ocurre un error.
"""

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

"""
    - operacion correcta    --> commit()
    - error --> rollback()
    - se cierra inmediatamente --> get_db()
"""
@contextmanager
def transaction(db: Session):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise




























