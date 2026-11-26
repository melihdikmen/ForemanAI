"""Shared pytest fixtures for API tests that hit the real (local) Postgres.

Each test runs inside an outer transaction that is rolled back at the end, so
tests can call endpoints that commit without leaving data behind.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.main import app
from app.db import engine


@pytest.fixture
def db_session() -> Iterator[Session]:
    """A session whose commits become savepoints inside a transaction we roll back."""
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """HTTP test client whose endpoints use the rollback-only session."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# Headers for the two roles in the fake (v1) header-based identity.
# User ids are ASCII on purpose: HTTP header values cannot carry characters like "ı".
TECHNICIAN_HEADERS = {"X-User": "ahmet.yilmaz", "X-Role": "technician"}
FOREMAN_HEADERS = {"X-User": "mehmet.kaya", "X-Role": "foreman"}
