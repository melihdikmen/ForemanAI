"""Database engine, session factory, and the declarative Base for all ORM models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class every ORM model inherits from; collects table metadata."""


# One engine per process: manages the connection pool to Postgres.
engine = create_engine(get_settings().database_url, echo=False)

# Session factory: call SessionLocal() to get a unit-of-work for queries.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
