from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES, STRENGTH_TYPE
from app.database import get_db
from app.models import (
    Activity,
    BodyComposition,
    DailySummary,
    NutritionDaily,
    PerformanceMetric,
    SleepSession,
)
from app.models.exercise_set import ExerciseSet
from app.models.stress_reading import StressReading
from app.models.training_readiness import TrainingReadiness
from app.models.user_goal import UserGoal
from app.schemas.plan import (
    PillarData,
    PillarDriver,
    PillarKPI,
    PlanDailyResponse,
    StripMetric,
)
from app.services.calculations import calculate_stress_last_hour

router = APIRouter(prefix="/api/plan", tags=["plan"])


def _fmt(val, decimals: int = 0) -> str:
    if val is None:
        return "--"
    if decimals == 0:
        return f"{int(round(val)):,}"
    return f"{val:.{decimals}f}"


def _fmt_duration_min(minutes: int | None) -> str:
    if minutes is None:
        return "--"
    h = minutes // 60
    m = minutes % 60
    return f"{h}:{m:02d}"


def _pct(value: float | None, target: float | None) -> int | None:
    if value is None or target is None or target == 0:
        return None
    return min(100, round(value / target * 100))


def _spark_7d(db: Session, model, column: str, target_date: date) -> list[float]:
    start = target_date - timedelta(days=6)
    rows = (
        db.query(getattr(model, column))
        .filter(model.date >= start, model.date <= target_date)
        .order_by(model.date)
        .all()
    )
    return [float(r[0]) for r in rows if r[0] is not None]


def _hrv_trend(db: Session, target_date: date, current_hrv: float | None) -> str:
    if current_hrv is None:
        return "flat"
    avg_7d = _spark_7d(db, SleepSession, "avg_hrv", target_date)
    if len(avg_7d) < 3:
        return "flat"
    recent_avg = sum(avg_7d) / len(avg_7d)
    if current_hrv > recent_avg * 1.03:
        return "up"
    if current_hrv < recent_avg * 0.97:
        return "down"
    return "flat"


def _tsb_label(tsb: float | None) -> str:
    if tsb is None:
        return ""
    if tsb > 10:
        return "fresh"
    if tsb > -10:
        return "neutral"
    if tsb > -30:
        return "building load"
    return "overreaching"


def _goal_val(goals: dict[str, UserGoal], key: str) -> float | None:
    g = goals.get(key)
    return g.target_value if g else None


def _build_strip(
    db: Session,
    target_date: date,
    daily: DailySummary | None,
    sleep: SleepSession | None,
    nutrition: NutritionDaily | None,
    perf: PerformanceMetric | None,
    goals: dict[str, UserGoal],
) -> list[StripMetric]:
    # Calories
    cal_val = nutrition.calories if nutrition else None
    cal_target = _goal_val(goals, "calories")

    # Protein
    prot_val = nutrition.protein_g if nutrition else None
    prot_target = _goal_val(goals, "protein")

    # Stress last hour
    readings = (
        db.query(StressReading.timestamp, StressReading.value)
        .filter(StressReading.date == target_date)
        .order_by(StressReading.timestamp)
        .all()
    )
    stress_1h = calculate_stress_last_hour(readings, datetime.now())
    stress_day_avg = daily.stress_avg if daily else None

    # HRV
    hrv_val = sleep.avg_hrv if sleep else None
    hrv_trend = _hrv_trend(db, target_date, hrv_val)
    hrv_7d = _spark_7d(db, SleepSession, "avg_hrv", target_date)
    hrv_7d_avg = round(sum(hrv_7d) / len(hrv_7d)) if hrv_7d else None

    # TSB
    tsb_val = perf.tsb if perf else None

    # Sleep
    sleep_min = sleep.total_sleep_min if sleep else None
    deep_pct = None
    if sleep and sleep.deep_min and sleep.total_sleep_min and sleep.total_sleep_min > 0:
        deep_pct = round(sleep.deep_min / sleep.total_sleep_min * 100)

    return [
        StripMetric(
            label="Calories",
            value=_fmt(cal_val),
            unit="kcal",
            target=_fmt(cal_target) if cal_target else None,
            pct=_pct(cal_val, cal_target),
        ),
        StripMetric(
            label="Protein",
            value=_fmt(prot_val),
            unit="g",
            target=_fmt(prot_target) if prot_target else None,
            pct=_pct(prot_val, prot_target),
        ),
        StripMetric(
            label="Stress 1h",
            value=_fmt(stress_1h),
            unit="avg",
            secondary_value=f"day avg: {_fmt(stress_day_avg)}" if stress_day_avg else None,
        ),
        StripMetric(
            label="HRV",
            value=_fmt(hrv_val),
            unit="ms",
            trend=hrv_trend,
            secondary_value=f"7d avg: {_fmt(hrv_7d_avg)}" if hrv_7d_avg else None,
        ),
        StripMetric(
            label="TSB",
            value=_fmt(tsb_val),
            unit="form",
            secondary_value=_tsb_label(tsb_val),
        ),
        StripMetric(
            label="Sleep",
            value=_fmt_duration_min(sleep_min),
            unit="hrs",
            secondary_value=f"deep {deep_pct}%" if deep_pct else None,
        ),
    ]


def _build_p1_aerobic(
    db: Session, target_date: date, perf: PerformanceMetric | None
) -> PillarData:
    vo2 = perf.vo2max if perf else None
    ctl = perf.ctl if perf else None
    atl = perf.atl if perf else None
    tsb = perf.tsb if perf else None

    # Weekly running stats
    start = target_date - timedelta(days=6)
    acts = (
        db.query(Activity)
        .filter(
            Activity.date >= start,
            Activity.date <= target_date,
            Activity.type.in_(RUNNING_TYPES),
        )
        .all()
    )
    weekly_km = round(sum((a.distance_m or 0) / 1000 for a in acts), 1)
    weekly_tss = round(sum(a.tss or 0 for a in acts), 0)

    return PillarData(
        id="aerobic",
        name="P1 Motor Aeróbico",
        color="#00d68f",
        collapsed_kpis=[
            PillarKPI(label="VO2max", value=_fmt(vo2, 1), unit="ml/kg"),
            PillarKPI(label="CTL", value=_fmt(ctl), unit=""),
            PillarKPI(label="VT1 pace", value="--", unit="min/km"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="VO2max",
                value=_fmt(vo2, 1),
                unit="ml/kg",
                target=">52",
                spark=_spark_7d(db, PerformanceMetric, "vo2max", target_date),
            ),
            PillarKPI(
                label="CTL",
                value=_fmt(ctl),
                unit="",
                target=">100",
                spark=_spark_7d(db, PerformanceMetric, "ctl", target_date),
            ),
            PillarKPI(label="VT1 pace", value="--", unit="min/km", target="<5:00"),
        ],
        drivers=[
            PillarDriver(label="km/week", value=_fmt(weekly_km, 1), unit="km"),
            PillarDriver(label="TSS/week", value=_fmt(weekly_tss), unit=""),
            PillarDriver(label="ATL", value=_fmt(atl), unit=""),
        ],
    )


def _build_p2_strength(db: Session, target_date: date) -> PillarData:
    start_7d = target_date - timedelta(days=6)
    start_30d = target_date - timedelta(days=30)

    # Weekly strength stats
    str_acts = (
        db.query(Activity)
        .filter(
            Activity.date >= start_7d,
            Activity.date <= target_date,
            Activity.type == STRENGTH_TYPE,
        )
        .all()
    )
    sess_count = len(str_acts)
    str_hours = round(sum((a.duration_sec or 0) / 3600 for a in str_acts), 1)

    # Days since last strength
    last = (
        db.query(Activity.date)
        .filter(Activity.type == STRENGTH_TYPE, Activity.date <= target_date)
        .order_by(Activity.date.desc())
        .first()
    )
    days_since = (target_date - last[0]).days if last else None

    # Pull-ups max from last 30 days
    str_act_ids = [
        a.id
        for a in db.query(Activity.id)
        .filter(
            Activity.date >= start_30d,
            Activity.date <= target_date,
            Activity.type == STRENGTH_TYPE,
        )
        .all()
    ]
    pullups = None
    if str_act_ids:
        result = (
            db.query(ExerciseSet.reps)
            .filter(
                ExerciseSet.activity_id.in_(str_act_ids),
                ExerciseSet.exercise_name.ilike("%pull%up%"),
                ExerciseSet.reps.isnot(None),
            )
            .order_by(ExerciseSet.reps.desc())
            .first()
        )
        pullups = result[0] if result else None

    return PillarData(
        id="strength",
        name="P2 Durabilidad Muscular",
        color="#00c4b4",
        collapsed_kpis=[
            PillarKPI(label="Pull-ups", value=_fmt(pullups), unit="reps"),
            PillarKPI(label="DL 5RM", value="--", unit="kg"),
            PillarKPI(label="Calf raises", value="--", unit="reps"),
        ],
        expanded_kpis=[
            PillarKPI(label="Pull-ups", value=_fmt(pullups), unit="reps", target="15"),
            PillarKPI(label="DL 5RM", value="--", unit="kg", target="103"),
            PillarKPI(label="Calf raises", value="--", unit="reps", target="30"),
        ],
        drivers=[
            PillarDriver(label="Sessions/wk", value=str(sess_count), unit="/2"),
            PillarDriver(label="Days since", value=_fmt(days_since), unit="days"),
            PillarDriver(label="Strength time", value=_fmt(str_hours, 1), unit="hrs"),
        ],
    )


def _build_p3_fueling(
    db: Session,
    target_date: date,
    nutrition: NutritionDaily | None,
    body_comp: BodyComposition | None,
) -> PillarData:
    weight = body_comp.weight_kg if body_comp else None
    bf = body_comp.body_fat_pct if body_comp else None

    # Glucose (latest)
    from app.models.glucose_daily import GlucoseDaily

    glucose = db.query(GlucoseDaily).filter_by(date=target_date).first()
    gluc_val = glucose.mean_glucose if glucose else None

    # 7d avg protein
    start = target_date - timedelta(days=6)
    prot_rows = (
        db.query(NutritionDaily.protein_g)
        .filter(NutritionDaily.date >= start, NutritionDaily.date <= target_date)
        .all()
    )
    prot_vals = [r[0] for r in prot_rows if r[0] is not None]
    prot_7d = round(sum(prot_vals) / len(prot_vals)) if prot_vals else None

    # 7d avg calories
    cal_rows = (
        db.query(NutritionDaily.calories)
        .filter(NutritionDaily.date >= start, NutritionDaily.date <= target_date)
        .all()
    )
    cal_vals = [r[0] for r in cal_rows if r[0] is not None]
    cal_7d = round(sum(cal_vals) / len(cal_vals)) if cal_vals else None

    return PillarData(
        id="fueling",
        name="P3 Fueling y Metabolismo",
        color="#b388ff",
        collapsed_kpis=[
            PillarKPI(label="Weight", value=_fmt(weight, 1), unit="kg"),
            PillarKPI(label="Body fat", value=_fmt(bf, 1) if bf else "--", unit="%"),
            PillarKPI(label="Glucose", value=_fmt(gluc_val), unit="mg/dL"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="Weight",
                value=_fmt(weight, 1),
                unit="kg",
                spark=_spark_7d(db, BodyComposition, "weight_kg", target_date),
            ),
            PillarKPI(
                label="Body fat",
                value=_fmt(bf, 1) if bf else "--",
                unit="%",
                target="<15%",
            ),
            PillarKPI(label="Glucose", value=_fmt(gluc_val), unit="mg/dL"),
        ],
        drivers=[
            PillarDriver(label="Cal avg 7d", value=_fmt(cal_7d), unit="kcal"),
            PillarDriver(label="Prot avg 7d", value=_fmt(prot_7d), unit="g"),
        ],
    )


def _build_p4_recovery(
    db: Session,
    target_date: date,
    daily: DailySummary | None,
    sleep: SleepSession | None,
    perf: PerformanceMetric | None,
) -> PillarData:
    hrv = sleep.avg_hrv if sleep else None
    sleep_min = sleep.total_sleep_min if sleep else None
    rhr = daily.resting_hr if daily else None
    sleep_score = sleep.sleep_score if sleep else None
    bb = daily.body_battery_high if daily else None
    stress = daily.stress_avg if daily else None

    deep_pct = None
    if sleep and sleep.deep_min and sleep.total_sleep_min and sleep.total_sleep_min > 0:
        deep_pct = round(sleep.deep_min / sleep.total_sleep_min * 100)

    bedtime = "--"
    if sleep and sleep.sleep_start:
        bedtime = sleep.sleep_start.strftime("%H:%M")

    return PillarData(
        id="recovery",
        name="P4 Recuperación",
        color="#f5c542",
        collapsed_kpis=[
            PillarKPI(label="HRV", value=_fmt(hrv), unit="ms"),
            PillarKPI(label="Sleep", value=_fmt_duration_min(sleep_min), unit="hrs"),
            PillarKPI(label="RHR", value=_fmt(rhr), unit="bpm"),
        ],
        expanded_kpis=[
            PillarKPI(
                label="Sleep total",
                value=_fmt_duration_min(sleep_min),
                unit="hrs",
                target=">7:30",
                spark=_spark_7d(db, SleepSession, "total_sleep_min", target_date),
            ),
            PillarKPI(
                label="Deep sleep",
                value=f"{deep_pct}%" if deep_pct else "--",
                unit="",
                target=">15%",
            ),
            PillarKPI(
                label="HRV baseline",
                value=_fmt(hrv),
                unit="ms",
                spark=_spark_7d(db, SleepSession, "avg_hrv", target_date),
            ),
        ],
        drivers=[
            PillarDriver(label="Sleep score", value=_fmt(sleep_score), unit=""),
            PillarDriver(label="Bedtime", value=bedtime, unit=""),
            PillarDriver(label="Body battery", value=_fmt(bb), unit="%"),
            PillarDriver(label="Stress avg", value=_fmt(stress), unit=""),
        ],
    )


def _build_p5_clinical(db: Session) -> PillarData:
    return PillarData(
        id="clinical",
        name="P5 Salud Clínica",
        color="#ff4d4d",
        collapsed_kpis=[
            PillarKPI(label="Screenings", value="✓", unit=""),
            PillarKPI(label="LDL", value="72", unit="mg/dL"),
            PillarKPI(label="Next", value="Ca coronario", unit=""),
        ],
        expanded_kpis=[
            PillarKPI(label="LDL", value="72", unit="mg/dL", target="<70"),
            PillarKPI(label="HDL", value="63", unit="mg/dL", target=">60", status="met"),
            PillarKPI(label="BP", value="--", unit="mmHg", target="<120/80"),
        ],
        drivers=[
            PillarDriver(label="Ca coronario", value="Pending", unit="before Sep 2026"),
            PillarDriver(label="Dermatología", value="Pending", unit="2026"),
        ],
    )


def _get_latest_date(db: Session) -> date:
    latest = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    return latest.date if latest else date.today()


@router.get("/daily", response_model=PlanDailyResponse)
def get_plan_daily(db: Session = Depends(get_db)):
    target = _get_latest_date(db)

    daily = db.query(DailySummary).filter_by(date=target).first()
    sleep = db.query(SleepSession).filter_by(date=target).first()
    nutrition = db.query(NutritionDaily).filter_by(date=target).first()
    perf = db.query(PerformanceMetric).filter_by(date=target).first()
    body_comp = db.query(BodyComposition).filter_by(date=target).first()

    all_goals = db.query(UserGoal).all()
    goals = {g.metric_key: g for g in all_goals}

    strip = _build_strip(db, target, daily, sleep, nutrition, perf, goals)

    pillars = [
        _build_p1_aerobic(db, target, perf),
        _build_p2_strength(db, target),
        _build_p3_fueling(db, target, nutrition, body_comp),
        _build_p4_recovery(db, target, daily, sleep, perf),
        _build_p5_clinical(db),
    ]

    return PlanDailyResponse(date=target, strip=strip, pillars=pillars)
