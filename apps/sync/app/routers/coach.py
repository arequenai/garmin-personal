"""Coach briefing endpoints."""
from __future__ import annotations

import datetime as dt
import logging
import os

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.coach import briefing as coach_briefing
from app.coach import persistence
from app.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/coach", tags=["coach"])


class TriggerRequest(BaseModel):
    force: bool = False
    date: dt.date | None = None


def _check_token(authorization: str | None) -> None:
    expected = os.environ.get("COACH_ADMIN_TOKEN", "")
    if not expected:
        raise HTTPException(status_code=503, detail="coach admin token not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="invalid bearer token")


@router.post("/trigger-briefing")
def trigger_briefing(
    body: TriggerRequest,
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    _check_token(authorization)
    target_date = body.date or dt.datetime.now().date()
    result = coach_briefing.run_pre_dinner(db, target_date=target_date, force=body.force)
    if result.skipped:
        raise HTTPException(
            status_code=409,
            detail={"error": "already_sent", "briefing_id": result.briefing_id},
        )
    return {
        "sent": result.sent,
        "briefing_id": result.briefing_id,
        "semaphore": result.semaphore,
        "flags": result.flags,
    }


@router.get("/last-briefing")
def last_briefing(db: Session = Depends(get_db)):
    row = persistence.get_last_briefing(db)
    if row is None:
        raise HTTPException(status_code=404, detail="no briefings yet")
    return {
        "date": row.date.isoformat(),
        "sent_at": row.sent_at.isoformat() if row.sent_at else None,
        "semaphore": row.semaphore,
        "flags": list(row.flags or []),
        "kind": row.kind,
    }
