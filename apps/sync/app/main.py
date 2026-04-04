from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings as app_settings
from app.routers import (
    activities,
    daily,
    dashboard,
    goals,
    nutrition,
    overview,
    performance,
    plan,
    settings,
    sleep,
    sync,
    tp,
)
from app.scheduler import scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(title="Garmin Personal Sync", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(activities.router)
app.include_router(sleep.router)
app.include_router(nutrition.router)
app.include_router(performance.router)
app.include_router(daily.router)
app.include_router(sync.router)
app.include_router(goals.router)
app.include_router(overview.router)
app.include_router(tp.router)
app.include_router(plan.router)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
