"""Database engine, session factory, and the declarative Base for all ORM models."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class every ORM model inherits from; collects table metadata."""


# Owner engine: manages the connection pool to Postgres with write privileges.
engine = create_engine(get_settings().database_url, echo=False)

# Session factory for code paths that may write (API endpoints, seed, indexing).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

# Read-only engine: connects as a Postgres role that only has SELECT.
# The agent's tools use this so that no matter what the LLM is talked into,
# the database itself rejects any write (least privilege, enforced by Postgres).
readonly_engine = create_engine(get_settings().database_url_readonly, echo=False)

# Session factory for the assistant's tools (fault history, manual search).
ReadOnlySessionLocal = sessionmaker(bind=readonly_engine, autoflush=False, expire_on_commit=False)
