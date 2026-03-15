from datetime import date

from pydantic import BaseModel


class KeyIndicator(BaseModel):
    label: str
    value: str
    unit: str
    trend_pct: float
    spark: list[float]


class KPI(BaseModel):
    label: str
    value: str
    unit: str
    trend_pct: float


class Driver(BaseModel):
    label: str
    value: str
    unit: str
    trend_pct: float


class OverviewCategoryResponse(BaseModel):
    score: int | None
    key_indicator: KeyIndicator | None
    kpis: list[KPI]
    drivers: list[Driver]


class DailyMetric(BaseModel):
    label: str
    value: str
    unit: str
    target: str
    pct: int


class DailySection(BaseModel):
    id: str
    label: str
    icon: str
    color: str
    metrics: list[DailyMetric]


class OverviewResponse(BaseModel):
    date: date
    categories: dict[str, OverviewCategoryResponse]
    daily_sections: list[DailySection]
