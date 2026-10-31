# Flow: request → get_db dependency → service/repository → commit/rollback.
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from contextlib import contextmanager

from app.core.config import settings

from sqlalchemy.orm import DeclarativeBase

# ---------------------------------------------------------
# ENGINE
# ---------------------------------------------------------

# The Engine is the connection infrastructure
# between SQLAlchemy and PostgreSQL.
#
# It uses the DATABASE_URL built in config.py:
#
# postgresql+psycopg://user:password@database:5432/aquaguard
#
# The Engine:
# - knows where PostgreSQL is;
# - uses psycopg as the driver;
# - manages a connection pool;
# - is shared by the whole application.

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

# ---------------------------------------------------------
# SESSION FACTORY
# ---------------------------------------------------------

# SessionLocal is NOT a session.
#
# It is a factory that creates new sessions when
# the application needs them.
#
# SessionLocal()
#       ↓
# A concrete Session
#
# Each request gets its own Session.

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)

# ---------------------------------------------------------
# FASTAPI DATABASE DEPENDENCY
# ---------------------------------------------------------
"""
Creates a Session for one operation/request.

Flow:

    SessionLocal()
          ↓
       Session
          ↓
        yield
          ↓
    FastAPI / Repository
          ↓
        close()

The finally block makes sure the session is closed
even if an error happens.
"""

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()

"""
    - operation succeeds --> commit()
    - error              --> rollback()
    - closing is done by --> get_db()
"""
@contextmanager
def transaction(db: Session):
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise

# ---------------------------------------------------------
#   SETUP ALEMBIC
# ---------------------------------------------------------
"""
    Every model inherits from this class (see the modules' model.py files)
"""
class Base(DeclarativeBase):
    pass
