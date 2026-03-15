from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.constants import RUNNING_TYPES, STRENGTH_TYPE
from app.database import get_db
from app.models import Activity, DailySummary, NutritionDaily, PerformanceMetric, SleepSession
from app.models.body_composition import BodyComposition
from app.models.exercise_set import ExerciseSet
from app.models.race_prediction import RacePrediction
from app.models.training_readiness import TrainingReadiness
from app.models.user_goal import UserGoal
from app.schemas.overview import (
    KPI,
    DailyMetric,
    DailySection,
    Driver,
    KeyIndicator,
    OverviewCategoryResponse,
    OverviewResponse,
)

router = APIRouter(prefix="/api/overview", tags=["overview"])


def _get_latest_date(db: Session) -> date:
    latest = db.query(DailySummary).order_by(DailySummary.date.desc()).first()
    return latest.date if latest else date.today()


def _trend_pct(current: float | None, previous: float | None) -> float:
    if current is None or previous is None or previous == 0:
        return 0.0
    return round((current - previous) / abs(previous) * 100, 1)


def _spark_values(db: Session, model, column, target_date: date, days: int = 7) -> list[float]:
    start = target_date - timedelta(days=days - 1)
    rows = (
        db.query(getattr(model, column))
        .filter(model.date >= start, model.date <= target_date)
        .order_by(model.date)
        .all()
    )
    return [float(r[0]) for r in rows if r[0] is not None]


def _get_value_days_ago(db: Session, model, column, target_date: date, days: int = 7):
    past_date = target_date - timedelta(days=days)
    row = db.query(getattr(model, column)).filter(model.date == past_date).first()
    return row[0] if row else None


def _fmt_duration_sec(seconds: int | None) -> str:
    if seconds is None:
        return "--"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}"


def _fmt_duration_min(minutes: int | None) -> str:
    if minutes is None:
        return "--"
    h = minutes // 60
    m = minutes % 60
    return f"{h}:{m:02d}"


def _fmt_time(dt) -> str:
    if dt is None:
        return "--"
    if hasattr(dt, "strftime"):
        return dt.strftime("%H:%M")
    return str(dt)


def _fmt_num(val, decimals: int = 0) -> str:
    if val is None:
        return "--"
    if decimals == 0:
        return f"{int(round(val)):,}"
    return f"{val:.{decimals}f}"


def _weekly_running_stats(db: Session, target_date: date) -> tuple[float, float]:
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
    total_km = sum((a.distance_m or 0) / 1000 for a in acts)
    total_elev = sum(a.elevation_gain or 0 for a in acts)
    return round(total_km, 1), round(total_elev, 0)


def _weekly_strength_stats(db: Session, target_date: date) -> tuple[int, float]:
    start = target_date - timedelta(days=6)
    acts = (
        db.query(Activity)
        .filter(
            Activity.date >= start,
            Activity.date <= target_date,
            Activity.type == STRENGTH_TYPE,
        )
        .all()
    )
    count = len(acts)
    total_hours = sum((a.duration_sec or 0) / 3600 for a in acts)
    return count, round(total_hours, 1)


def _top_1rm(db: Session, activity_ids: list[int]) -> dict[str, float]:
    """Compute top Epley 1RM for key exercises from recent exercise sets."""
    if not activity_ids:
        return {}
    sets = (
        db.query(ExerciseSet)
        .filter(
            ExerciseSet.activity_id.in_(activity_ids),
            ExerciseSet.weight_kg.isnot(None),
            ExerciseSet.reps.isnot(None),
            ExerciseSet.reps > 0,
        )
        .all()
    )
    results: dict[str, float] = {}
    for s in sets:
        one_rm = s.weight_kg * (1 + s.reps / 30)
        name_lower = s.exercise_name.lower()
        # Match key exercises
        for key in ("bench", "squat", "deadlift"):
            if key in name_lower:
                if key not in results or one_rm > results[key]:
                    results[key] = round(one_rm, 1)
                break
    return results


def _pullup_max(db: Session, activity_ids: list[int]) -> int | None:
    """Find max reps for pull-up exercises (bodyweight)."""
    if not activity_ids:
        return None
    sets = (
        db.query(ExerciseSet.reps)
        .filter(
            ExerciseSet.activity_id.in_(activity_ids),
            ExerciseSet.exercise_name.ilike("%pull%up%"),
            ExerciseSet.reps.isnot(None),
        )
        .order_by(ExerciseSet.reps.desc())
        .first()
    )
    return sets[0] if sets else None


def _pct_toward_goal(
    value: float | None, target: float | None, lower_is_better: bool = False
) -> int:
    if value is None or target is None or target == 0:
        return 0
    if lower_is_better:
        return min(100, round(target / value * 100)) if value != 0 else 0
    return min(100, round(value / target * 100))


def _build_running(
    db: Session, target_date: date, perf, goals: dict
) -> OverviewCategoryResponse:
    race = db.query(RacePrediction).filter_by(date=target_date).first()
    race_7ago = _get_value_days_ago(db, RacePrediction, "predicted_marathon_sec", target_date, 7)

    marathon_val = race.predicted_marathon_sec if race else None
    spark = _spark_values(db, RacePrediction, "predicted_marathon_sec", target_date)

    weekly_km, weekly_elev = _weekly_running_stats(db, target_date)
    prev_km, prev_elev = _weekly_running_stats(db, target_date - timedelta(days=7))

    vo2max = perf.vo2max if perf else None
    vo2max_7ago = _get_value_days_ago(db, PerformanceMetric, "vo2max", target_date, 7)

    ctl = perf.ctl if perf else None
    ctl_7ago = _get_value_days_ago(db, PerformanceMetric, "ctl", target_date, 7)
    atl = perf.atl if perf else None
    atl_7ago = _get_value_days_ago(db, PerformanceMetric, "atl", target_date, 7)

    pred_5k = race.predicted_5k_sec if race else None
    pred_5k_7ago = _get_value_days_ago(db, RacePrediction, "predicted_5k_sec", target_date, 7)

    # Category score from perf
    scores = (perf.category_scores or {}) if perf else {}

    return OverviewCategoryResponse(
        score=scores.get("running"),
        key_indicator=KeyIndicator(
            label="Marathon Time",
            value=_fmt_duration_sec(marathon_val),
            unit="",
            trend_pct=_trend_pct(marathon_val, race_7ago),
            spark=spark,
        )
        if marathon_val
        else None,
        kpis=[
            KPI(
                label="VO2max",
                value=_fmt_num(vo2max, 1),
                unit="ml/kg/min",
                trend_pct=_trend_pct(vo2max, vo2max_7ago),
            ),
            KPI(
                label="CTL",
                value=_fmt_num(ctl),
                unit="",
                trend_pct=_trend_pct(ctl, ctl_7ago),
            ),
            KPI(
                label="Predicted 5K",
                value=_fmt_duration_sec(pred_5k),
                unit="",
                trend_pct=_trend_pct(pred_5k, pred_5k_7ago),
            ),
        ],
        drivers=[
            Driver(
                label="KM Run",
                value=_fmt_num(weekly_km, 1),
                unit="km/wk",
                trend_pct=_trend_pct(weekly_km, prev_km),
            ),
            Driver(
                label="Elevation",
                value=_fmt_num(weekly_elev),
                unit="m",
                trend_pct=_trend_pct(weekly_elev, prev_elev),
            ),
            Driver(
                label="ATL",
                value=_fmt_num(atl),
                unit="",
                trend_pct=_trend_pct(atl, atl_7ago),
            ),
        ],
    )


def _build_strength(
    db: Session,
    target_date: date,
    perf,
    body_comp,
    strength_act_ids=None,
    weekly_strength=None,
) -> OverviewCategoryResponse:
    scores = (perf.category_scores or {}) if perf else {}

    muscle = body_comp.muscle_mass_kg if body_comp else None
    muscle_7ago = _get_value_days_ago(db, BodyComposition, "muscle_mass_kg", target_date, 7)
    spark = _spark_values(db, BodyComposition, "muscle_mass_kg", target_date)

    # Use pre-fetched strength activity IDs or query
    if strength_act_ids is None:
        start_30d = target_date - timedelta(days=30)
        strength_acts = (
            db.query(Activity.id)
            .filter(
                Activity.date >= start_30d,
                Activity.date <= target_date,
                Activity.type == STRENGTH_TYPE,
            )
            .all()
        )
        strength_act_ids = [a[0] for a in strength_acts]
    top_1rms = _top_1rm(db, strength_act_ids)
    pullups = _pullup_max(db, strength_act_ids)

    if weekly_strength is None:
        weekly_strength = _weekly_strength_stats(db, target_date)
    str_count, str_hours = weekly_strength
    prev_count, prev_hours = _weekly_strength_stats(db, target_date - timedelta(days=7))

    # Get today's protein from nutrition
    nutrition = db.query(NutritionDaily).filter_by(date=target_date).first()
    protein = nutrition.protein_g if nutrition else None
    protein_7ago = _get_value_days_ago(db, NutritionDaily, "protein_g", target_date, 7)

    kpis = []
    if "bench" in top_1rms:
        kpis.append(
            KPI(
                label="Bench 1RM",
                value=_fmt_num(top_1rms["bench"]),
                unit="kg",
                trend_pct=0,
            )
        )
    if pullups is not None:
        kpis.append(
            KPI(label="Pull-ups", value=str(pullups), unit="reps", trend_pct=0)
        )
    if "squat" in top_1rms:
        kpis.append(
            KPI(
                label="Squat 1RM",
                value=_fmt_num(top_1rms["squat"]),
                unit="kg",
                trend_pct=0,
            )
        )
    # Fill to 3 KPIs
    while len(kpis) < 3:
        kpis.append(KPI(label="--", value="--", unit="", trend_pct=0))

    return OverviewCategoryResponse(
        score=scores.get("strength"),
        key_indicator=KeyIndicator(
            label="Muscle Mass",
            value=_fmt_num(muscle, 1),
            unit="kg",
            trend_pct=_trend_pct(muscle, muscle_7ago),
            spark=spark,
        )
        if muscle
        else None,
        kpis=kpis[:3],
        drivers=[
            Driver(
                label="Sessions",
                value=str(str_count),
                unit="/wk",
                trend_pct=_trend_pct(str_count, prev_count),
            ),
            Driver(
                label="Strength Time",
                value=_fmt_num(str_hours, 1),
                unit="hrs",
                trend_pct=_trend_pct(str_hours, prev_hours),
            ),
            Driver(
                label="Protein",
                value=_fmt_num(protein),
                unit="g/day",
                trend_pct=_trend_pct(protein, protein_7ago),
            ),
        ],
    )


def _build_recovery(
    db: Session, target_date: date, perf, daily, sleep, tr=None
) -> OverviewCategoryResponse:
    scores = (perf.category_scores or {}) if perf else {}
    if tr is None:
        tr = db.query(TrainingReadiness).filter_by(date=target_date).first()
    tr_score = tr.score if tr else None
    tr_7ago = _get_value_days_ago(db, TrainingReadiness, "score", target_date, 7)
    spark = _spark_values(db, TrainingReadiness, "score", target_date)

    rhr = daily.resting_hr if daily else None
    rhr_7ago = _get_value_days_ago(db, DailySummary, "resting_hr", target_date, 7)

    hrv = sleep.avg_hrv if sleep else None
    hrv_7ago = _get_value_days_ago(db, SleepSession, "avg_hrv", target_date, 7)

    tsb = perf.tsb if perf else None
    tsb_7ago = _get_value_days_ago(db, PerformanceMetric, "tsb", target_date, 7)

    sleep_score = sleep.sleep_score if sleep else None
    stress_avg = daily.stress_avg if daily else None
    bb_high = daily.body_battery_high if daily else None

    return OverviewCategoryResponse(
        score=scores.get("recovery"),
        key_indicator=KeyIndicator(
            label="Recovery Score",
            value=_fmt_num(tr_score),
            unit="%",
            trend_pct=_trend_pct(tr_score, tr_7ago),
            spark=spark,
        )
        if tr_score
        else None,
        kpis=[
            KPI(
                label="RHR",
                value=_fmt_num(rhr),
                unit="bpm",
                trend_pct=_trend_pct(rhr, rhr_7ago),
            ),
            KPI(
                label="HRV",
                value=_fmt_num(hrv),
                unit="ms",
                trend_pct=_trend_pct(hrv, hrv_7ago),
            ),
            KPI(
                label="TSB",
                value=_fmt_num(tsb),
                unit="",
                trend_pct=_trend_pct(tsb, tsb_7ago),
            ),
        ],
        drivers=[
            Driver(label="Sleep Score", value=_fmt_num(sleep_score), unit="", trend_pct=0),
            Driver(label="Stress", value=_fmt_num(stress_avg), unit="avg", trend_pct=0),
            Driver(label="Battery", value=_fmt_num(bb_high), unit="%", trend_pct=0),
        ],
    )


def _build_sleep(
    db: Session, target_date: date, perf, sleep, daily
) -> OverviewCategoryResponse:
    scores = (perf.category_scores or {}) if perf else {}

    sleep_score = sleep.sleep_score if sleep else None
    sleep_score_7ago = _get_value_days_ago(db, SleepSession, "sleep_score", target_date, 7)
    spark = _spark_values(db, SleepSession, "sleep_score", target_date)

    total_min = sleep.total_sleep_min if sleep else None
    awake_min = sleep.awake_min if sleep else None
    efficiency = None
    if total_min and awake_min is not None and (total_min + awake_min) > 0:
        efficiency = round(total_min / (total_min + awake_min) * 100)

    bb_high = daily.body_battery_high if daily else None

    deep_pct = None
    if sleep and sleep.deep_min and sleep.total_sleep_min and sleep.total_sleep_min > 0:
        deep_pct = round(sleep.deep_min / sleep.total_sleep_min * 100)

    hrv = sleep.avg_hrv if sleep else None
    sleep_start = _fmt_time(sleep.sleep_start if sleep else None)

    return OverviewCategoryResponse(
        score=scores.get("sleep"),
        key_indicator=KeyIndicator(
            label="Sleep Score",
            value=_fmt_num(sleep_score),
            unit="",
            trend_pct=_trend_pct(sleep_score, sleep_score_7ago),
            spark=spark,
        )
        if sleep_score
        else None,
        kpis=[
            KPI(
                label="Time in Bed",
                value=_fmt_duration_min(total_min),
                unit="hrs",
                trend_pct=0,
            ),
            KPI(
                label="Efficiency",
                value=_fmt_num(efficiency),
                unit="%",
                trend_pct=0,
            ),
            KPI(
                label="Body Battery",
                value=_fmt_num(bb_high),
                unit="",
                trend_pct=0,
            ),
        ],
        drivers=[
            Driver(label="Sleep Start", value=sleep_start, unit="", trend_pct=0),
            Driver(
                label="Deep Sleep",
                value=f"{deep_pct}%" if deep_pct else "--",
                unit="",
                trend_pct=0,
            ),
            Driver(label="HRV", value=_fmt_num(hrv), unit="ms", trend_pct=0),
        ],
    )


def _build_body(
    db: Session, target_date: date, perf, body_comp, nutrition
) -> OverviewCategoryResponse:
    scores = (perf.category_scores or {}) if perf else {}

    bf = body_comp.body_fat_pct if body_comp else None
    bf_7ago = _get_value_days_ago(db, BodyComposition, "body_fat_pct", target_date, 7)
    spark = _spark_values(db, BodyComposition, "body_fat_pct", target_date)

    weight = body_comp.weight_kg if body_comp else None
    muscle = body_comp.muscle_mass_kg if body_comp else None
    bmi = body_comp.bmi if body_comp else None

    cals = nutrition.calories if nutrition else None
    protein = nutrition.protein_g if nutrition else None
    fat = nutrition.fat_g if nutrition else None

    return OverviewCategoryResponse(
        score=scores.get("body"),
        key_indicator=KeyIndicator(
            label="Body Fat",
            value=_fmt_num(bf, 1),
            unit="%",
            trend_pct=_trend_pct(bf, bf_7ago),
            spark=spark,
        )
        if bf
        else None,
        kpis=[
            KPI(
                label="Weight",
                value=_fmt_num(weight, 1),
                unit="kg",
                trend_pct=0,
            ),
            KPI(
                label="Muscle Mass",
                value=_fmt_num(muscle, 1),
                unit="kg",
                trend_pct=0,
            ),
            KPI(label="BMI", value=_fmt_num(bmi, 1), unit="", trend_pct=0),
        ],
        drivers=[
            Driver(
                label="Calories",
                value=_fmt_num(cals),
                unit="kcal",
                trend_pct=0,
            ),
            Driver(
                label="Protein",
                value=_fmt_num(protein),
                unit="g/day",
                trend_pct=0,
            ),
            Driver(label="Fat", value=_fmt_num(fat), unit="g", trend_pct=0),
        ],
    )


def _build_glucose() -> OverviewCategoryResponse:
    return OverviewCategoryResponse(score=None, key_indicator=None, kpis=[], drivers=[])


def _build_daily_sections(
    db: Session,
    target_date: date,
    daily,
    sleep,
    perf,
    body_comp,
    nutrition,
    goals: dict,
    tr=None,
    strength_act_ids=None,
    weekly_strength=None,
) -> list[DailySection]:
    sections = []

    def _goal(key: str) -> float | None:
        g = goals.get(key)
        return g.target_value if g else None

    def _daily_metric(
        label: str,
        value,
        unit: str,
        goal_key: str,
        lower_is_better: bool = False,
    ) -> DailyMetric:
        target = _goal(goal_key)
        val = float(value) if value is not None else None
        pct = _pct_toward_goal(val, target, lower_is_better)
        return DailyMetric(
            label=label,
            value=_fmt_num(value, 1)
            if isinstance(value, float) and value != int(value)
            else _fmt_num(value),
            unit=unit,
            target=_fmt_num(target, 1)
            if target and target != int(target)
            else _fmt_num(target)
            if target
            else "--",
            pct=pct,
        )

    # Nutrition section
    sections.append(
        DailySection(
            id="nutrition",
            label="Nutrition",
            icon="\U0001f37d\ufe0f",
            color="whoop-green",
            metrics=[
                _daily_metric(
                    "Calories",
                    nutrition.calories if nutrition else None,
                    "kcal",
                    "calories",
                ),
                _daily_metric(
                    "Weight",
                    body_comp.weight_kg if body_comp else None,
                    "kg",
                    "weight",
                ),
                _daily_metric(
                    "Carbs",
                    nutrition.carbs_g if nutrition else None,
                    "g",
                    "carbs",
                ),
                _daily_metric(
                    "Protein",
                    nutrition.protein_g if nutrition else None,
                    "g",
                    "protein",
                ),
            ],
        )
    )

    # Recovery section
    if tr is None:
        tr = db.query(TrainingReadiness).filter_by(date=target_date).first()
    sections.append(
        DailySection(
            id="recovery",
            label="Recovery",
            icon="\U0001f50b",
            color="whoop-yellow",
            metrics=[
                _daily_metric(
                    "Recovery",
                    tr.score if tr else None,
                    "%",
                    "recovery_score",
                ),
                _daily_metric(
                    "Battery",
                    daily.body_battery_high if daily else None,
                    "%",
                    "body_battery",
                ),
                _daily_metric(
                    "Sleep Quality",
                    sleep.sleep_score if sleep else None,
                    "",
                    "sleep_score",
                ),
                _daily_metric(
                    "HRV",
                    sleep.avg_hrv if sleep else None,
                    "ms",
                    "hrv",
                ),
            ],
        )
    )

    # Running section
    marathon_sec = (
        db.query(RacePrediction.predicted_marathon_sec)
        .filter_by(date=target_date)
        .scalar()
    )
    marathon_goal = _goal("marathon")
    sections.append(
        DailySection(
            id="running",
            label="Running",
            icon="\U0001f3c3",
            color="whoop-green",
            metrics=[
                _daily_metric(
                    "TSB", perf.tsb if perf else None, "", "tsb"
                ),
                _daily_metric(
                    "CTL", perf.ctl if perf else None, "", "ctl"
                ),
                DailyMetric(
                    label="Marathon",
                    value=_fmt_duration_sec(marathon_sec),
                    unit="",
                    target=_fmt_duration_sec(int(marathon_goal))
                    if marathon_goal
                    else "--",
                    pct=min(
                        100,
                        round(
                            (marathon_goal or 0)
                            / max(1, marathon_sec or 99999)
                            * 100
                        ),
                    )
                    if marathon_goal
                    else 0,
                ),
                _daily_metric(
                    "VO2max",
                    perf.vo2max if perf else None,
                    "",
                    "vo2max",
                ),
            ],
        )
    )

    # Strength section
    if weekly_strength is None:
        weekly_strength = _weekly_strength_stats(db, target_date)
    str_count, str_hours = weekly_strength
    if strength_act_ids is None:
        start_30d = target_date - timedelta(days=30)
        strength_act_ids = [
            a[0]
            for a in db.query(Activity.id)
            .filter(
                Activity.date >= start_30d,
                Activity.date <= target_date,
                Activity.type == STRENGTH_TYPE,
            )
            .all()
        ]
    pullups = _pullup_max(db, strength_act_ids)
    sections.append(
        DailySection(
            id="strength",
            label="Strength",
            icon="\U0001f4aa",
            color="whoop-teal",
            metrics=[
                _daily_metric("Pull-ups Max", pullups, "reps", "pullups"),
                _daily_metric(
                    "Strength Time", str_hours, "hrs", "strength_time"
                ),
                _daily_metric(
                    "Muscle Mass",
                    body_comp.muscle_mass_kg if body_comp else None,
                    "kg",
                    "muscle_mass",
                ),
                _daily_metric(
                    "Training Days", str_count, "/wk", "strength_days"
                ),
            ],
        )
    )

    # Body Comp section
    sections.append(
        DailySection(
            id="body",
            label="Body Comp",
            icon="\u2696\ufe0f",
            color="whoop-purple",
            metrics=[
                _daily_metric(
                    "Body Fat",
                    body_comp.body_fat_pct if body_comp else None,
                    "%",
                    "body_fat",
                    lower_is_better=True,
                ),
                _daily_metric(
                    "BMI",
                    body_comp.bmi if body_comp else None,
                    "",
                    "bmi",
                    lower_is_better=True,
                ),
                _daily_metric(
                    "Body Water",
                    body_comp.body_water_pct if body_comp else None,
                    "%",
                    "body_water",
                ),
                _daily_metric(
                    "Visceral Fat",
                    body_comp.visceral_fat if body_comp else None,
                    "",
                    "visceral_fat",
                    lower_is_better=True,
                ),
            ],
        )
    )

    return sections


@router.get("", response_model=OverviewResponse)
def get_overview(db: Session = Depends(get_db)):
    target = _get_latest_date(db)

    daily = db.query(DailySummary).filter_by(date=target).first()
    sleep = db.query(SleepSession).filter_by(date=target).first()
    perf = db.query(PerformanceMetric).filter_by(date=target).first()
    nutrition = db.query(NutritionDaily).filter_by(date=target).first()
    body_comp = db.query(BodyComposition).filter_by(date=target).first()

    # Goals as dict
    all_goals = db.query(UserGoal).all()
    goals = {g.metric_key: g for g in all_goals}

    # Pre-fetch shared data to avoid duplicate queries
    tr = db.query(TrainingReadiness).filter_by(date=target).first()
    weekly_strength = _weekly_strength_stats(db, target)
    start_30d = target - timedelta(days=30)
    strength_act_ids = [
        a[0]
        for a in db.query(Activity.id)
        .filter(
            Activity.date >= start_30d,
            Activity.date <= target,
            Activity.type == STRENGTH_TYPE,
        )
        .all()
    ]

    categories = {
        "running": _build_running(db, target, perf, goals),
        "strength": _build_strength(
            db, target, perf, body_comp, strength_act_ids, weekly_strength
        ),
        "recovery": _build_recovery(db, target, perf, daily, sleep, tr),
        "sleep": _build_sleep(db, target, perf, sleep, daily),
        "body": _build_body(db, target, perf, body_comp, nutrition),
        "glucose": _build_glucose(),
    }

    daily_sections = _build_daily_sections(
        db, target, daily, sleep, perf, body_comp, nutrition, goals, tr,
        strength_act_ids, weekly_strength,
    )

    return OverviewResponse(
        date=target,
        categories=categories,
        daily_sections=daily_sections,
    )
