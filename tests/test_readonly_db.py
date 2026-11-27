"""Prove the least-privilege boundary: the assistant's DB role cannot write.

This is enforced by Postgres (GRANT SELECT only), not by our Python code, so even
a successful prompt injection that makes the LLM "want" to write has no effect.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import ProgrammingError

from app.db import ReadOnlySessionLocal
from app.models import Machine


def test_readonly_role_can_select() -> None:
    """The reader role must still be able to read the tables the tools need."""
    with ReadOnlySessionLocal() as session:
        machine_count = session.scalar(select(Machine.id).limit(1))
    assert machine_count is not None


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO machines (code, name, location) VALUES ('X-1', 'x', 'x')",
        "UPDATE machines SET name = 'hacked'",
        "DELETE FROM fault_records",
        "DROP TABLE work_orders",
    ],
)
def test_readonly_role_cannot_write(statement: str) -> None:
    """Every write/DDL statement must be rejected with a permission error."""
    with ReadOnlySessionLocal() as session, pytest.raises(ProgrammingError) as error:
        session.execute(text(statement))
        session.commit()
    assert "permission denied" in str(error.value) or "must be owner" in str(error.value)
