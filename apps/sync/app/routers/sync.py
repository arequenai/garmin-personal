from datetime import date, timedelta

from fastapi import APIRouter, BackgroundTasks

from app.services.sync_orchestrator import run_sync_for_date

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("/trigger")
def trigger_sync(
    background_tasks: BackgroundTasks,
    days_back: int = 1,
):
    target = date.today() - timedelta(days=days_back)
    background_tasks.add_task(run_sync_for_date, target)
    return {"status": "sync_started", "target_date": target.isoformat()}
