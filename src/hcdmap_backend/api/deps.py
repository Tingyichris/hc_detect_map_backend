from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..db import get_db
from ..settings import settings

DbDep = Depends(get_db)


def require_service_token(authorization: str = Header(default="")) -> None:
    """Auth for the server -> backend ingest feed (shared secret)."""
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.service_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "bad service token")


def require_user(authorization: str = Header(default="")) -> dict:
    """Auth for frontend calls. STUB — wire to auth/tokens.py (JWT, roles floor|manager)."""
    if not authorization:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "login required")
    return {"sub": "dev", "role": "manager"}


__all__ = ["get_db", "Session", "require_service_token", "require_user"]
