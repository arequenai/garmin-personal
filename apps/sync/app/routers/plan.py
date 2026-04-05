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
from app.models.tp_fitness_data import TPFitnessData
from app.models.user_goal import UserGoal
from app.schemas.plan import (
    PillarData,
    PillarDriver,
    PillarKPI,
    PlanDailyResponse,
    StripMetric,
    SyncSourceStatus,
)
from app.services.calculations import calculate_stress_last_hour
from app.services.calorie_target import fetch_and_compute_targets

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
    tp_fitness: TPFitnessData | None,
    perf: PerformanceMetric | None,
    goals: dict[str, UserGoal],
) -> list[StripMetric]:
    # Calories — use adaptive target, fall back to MFP goal, then user_goals
    cal_val = nutrition.calories if nutrition else None
    adaptive_targets = fetch_and_compute_targets(
        db, target_date - timedelta(days=1), target_date
    )
    cal_target_adaptive = adaptive_targets.get(target_date)
    cal_goal = nutrition.calories_goal if nutrition and nutrition.calories_goal else None
    cal_target = cal_target_adaptive or cal_goal or _goal_val(goals, "calories")

    # Protein — prefer MFP daily goal, fall back to user_goals
    prot_val = nutrition.protein_g if nutrition else None
    prot_goal = nutrition.protein_goal_g if nutrition and nutrition.protein_goal_g else None
    prot_target = prot_goal or _goal_val(goals, "protein")

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

    # TSB — from TrainingPeaks only
    tsb_val = tp_fitness.tsb if tp_fitness else None

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
    db: Session,
    target_date: date,
    tp_fitness: TPFitnessData | None,
    perf: PerformanceMetric | None,
) -> PillarData:
    vo2 = perf.vo2max if perf else None
    # CTL/ATL from TrainingPeaks only
    ctl = tp_fitness.ctl if tp_fitness else None
    atl = tp_fitness.atl if tp_fitness else None

    # Weekly TSS from TP completed workouts
    start = target_date - timedelta(days=6)
    from app.models.tp_completed_workout import TPCompletedWorkout

    tp_workouts = (
        db.query(TPCompletedWorkout)
        .filter(TPCompletedWorkout.date >= start, TPCompletedWorkout.date <= target_date)
        .all()
    )
    weekly_tss = round(sum(w.tss or 0 for w in tp_workouts), 0)

    # Weekly km from Garmin activities (GPS source)
    run_acts = (
        db.query(Activity)
        .filter(
            Activity.date >= start,
            Activity.date <= target_date,
            Activity.type.in_(RUNNING_TYPES),
        )
        .all()
    )
    weekly_km = round(sum((a.distance_m or 0) / 1000 for a in run_acts), 1)

    return PillarData(
        id="aerobic",
        name="Aeróbico",
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
                spark=_spark_7d(db, TPFitnessData, "ctl", target_date),
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
        name="Muscular",
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
        name="Nutrición",
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
        name="Recuperación",
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
        name="Clínica",
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


def _latest_or_today(db: Session, model, target: date):
    """Return today's row if it exists, otherwise the most recent row."""
    row = db.query(model).filter(model.date == target).first()
    if row:
        return row, target
    row = db.query(model).filter(model.date <= target).order_by(model.date.desc()).first()
    return row, (row.date if row else None)


@router.get("/daily", response_model=PlanDailyResponse)
def get_plan_daily(db: Session = Depends(get_db)):
    target = date.today()

    daily, daily_date = _latest_or_today(db, DailySummary, target)
    sleep, sleep_date = _latest_or_today(db, SleepSession, target)
    nutrition, nutrition_date = _latest_or_today(db, NutritionDaily, target)
    perf, perf_date = _latest_or_today(db, PerformanceMetric, target)
    body_comp, body_comp_date = _latest_or_today(db, BodyComposition, target)
    tp_fitness, tp_fitness_date = _latest_or_today(db, TPFitnessData, target)

    all_goals = db.query(UserGoal).all()
    goals = {g.metric_key: g for g in all_goals}

    strip = _build_strip(db, target, daily, sleep, nutrition, tp_fitness, perf, goals)

    pillars = [
        _build_p1_aerobic(db, target, tp_fitness, perf),
        _build_p2_strength(db, target),
        _build_p3_fueling(db, target, nutrition, body_comp),
        _build_p4_recovery(db, target, daily, sleep, perf),
        _build_p5_clinical(db),
    ]

    sync_status = [
        SyncSourceStatus(source="Garmin", last_date=daily_date, ok=daily_date == target),
        SyncSourceStatus(source="Sleep", last_date=sleep_date, ok=sleep_date == target),
        SyncSourceStatus(source="MFP", last_date=nutrition_date, ok=nutrition_date == target),
        SyncSourceStatus(source="TrainingPeaks", last_date=tp_fitness_date, ok=tp_fitness_date == target),
    ]

    return PlanDailyResponse(date=target, strip=strip, pillars=pillars, sync_status=sync_status)
