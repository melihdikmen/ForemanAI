"""Shared FastAPI dependencies: database session and the (fake, v1) current user.

WARNING: identity comes from plain request headers (X-User / X-Role). Anyone can
send any header, so this is NOT real authentication. It only models roles so the
approval flow can be built and tested; production would use SSO (e.g. Entra ID).
"""

from __future__ import annotations

import enum
from collections.abc import Callable, Iterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import SessionLocal


class Role(enum.StrEnum):
    """What a user is allowed to do in the work-order flow."""

    TECHNICIAN = "technician"  # asks questions, submits drafts for approval
    FOREMAN = "foreman"  # reviews pending work orders: approve or reject


class CurrentUser(BaseModel):
    """The caller of the current request."""

    name: str
    role: Role


def get_db() -> Iterator[Session]:
    """Open one DB session per request and always close it afterwards."""
    session = SessionLocal()
    try:
        yield session  # the endpoint runs here
    finally:
        session.close()


def get_current_user(
    x_user: Annotated[str | None, Header()] = None,
    x_role: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """Read the caller's name and role from headers; 401 if missing or unknown."""
    if not x_user or not x_role:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "X-User and X-Role headers required")
    try:
        role = Role(x_role)
    except ValueError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, f"unknown role: {x_role}") from exc
    return CurrentUser(name=x_user, role=role)


def require_role(required_role: Role) -> Callable[..., CurrentUser]:
    """Build a dependency that lets only users with `required_role` through.

    Usage: `user: Annotated[CurrentUser, Depends(require_role(Role.FOREMAN))]`.
    Missing identity -> 401 (from get_current_user); wrong role -> 403.
    """

    def check_role(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        """Return the user if their role matches, otherwise raise 403 Forbidden."""
        if user.role != required_role:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, f"requires role '{required_role}', got '{user.role}'"
            )
        return user

    return check_role
