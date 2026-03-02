import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


def _build_db_url() -> str:
    """
    Build a SQLAlchemy DB URL from environment variables.

    Expected env vars (provided via .env in this container):
    - POSTGRES_URL
    - POSTGRES_USER
    - POSTGRES_PASSWORD
    - POSTGRES_DB
    - POSTGRES_PORT
    """
    host = os.getenv("POSTGRES_URL", "localhost")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")
    db = os.getenv("POSTGRES_DB", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")

    # psycopg2 driver
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"


_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


# PUBLIC_INTERFACE
def get_engine() -> Engine:
    """Return a singleton SQLAlchemy Engine configured via environment variables."""
    global _ENGINE, _SessionLocal
    if _ENGINE is None:
        _ENGINE = create_engine(_build_db_url(), pool_pre_ping=True)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE)
    return _ENGINE


# PUBLIC_INTERFACE
def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a SQLAlchemy Session and ensures it is closed."""
    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
