"""
Synchronous SQLAlchemy session for Celery workers.

API layer uses async SQLAlchemy; workers use a sync driver (psycopg2).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


def _sync_url(url: str) -> str:
    if "+asyncpg" in url:
        return url.replace("+asyncpg", "+psycopg2", 1)
    return url


settings = get_settings()
sync_engine = create_engine(
    _sync_url(settings.database_url),
    pool_pre_ping=True,
)
SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, expire_on_commit=False)


def sync_session() -> Session:
    return SyncSessionLocal()
