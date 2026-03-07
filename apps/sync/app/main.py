from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    activities,
    daily,
    dashboard,
    nutrition,
    performance,
    settings,
    sleep,
    sync,
)

app = FastAPI(title="Garmin Personal Sync")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
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


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
