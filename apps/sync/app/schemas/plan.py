from datetime import date

from pydantic import BaseModel


class StripMetric(BaseModel):
    label: str
    value: str
    secondary_value: str | None = None
    unit: str
    target: str | None = None
    pct: int | None = None
    trend: str | None = None  # "up", "down", "flat"


class PillarKPI(BaseModel):
    label: str
    value: str
    unit: str
    target: str | None = None
    status: str | None = None  # "on_track", "behind", "met"
    spark: list[float] = []


class PillarDriver(BaseModel):
    label: str
    value: str
    unit: str


class PillarData(BaseModel):
    id: str
    name: str
    color: str
    collapsed_kpis: list[PillarKPI]
    expanded_kpis: list[PillarKPI] = []
    drivers: list[PillarDriver] = []


class SyncSourceStatus(BaseModel):
    source: str
    last_date: date | None = None
    ok: bool


class PlanDailyResponse(BaseModel):
    date: date
    strip: list[StripMetric]
    pillars: list[PillarData]
    sync_status: list[SyncSourceStatus] = []
