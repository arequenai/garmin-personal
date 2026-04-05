from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models import DailySummary, NutritionDaily
from app.models.tp_planned_workout import TPPlannedWorkout
from app.models.user_goal import UserGoal


@dataclass
class CalorieTargetConfig:
    sedentary: int = 1800
    deficit: int = 300
    exercise_today_weight: float = 0.5
    exercise_avg_weight: float = 0.3
    excess_carryover: float = 0.5
    preload_bonus: int = 200
    preload_threshold_sec: int = 7200
    floor: int = 1200


def compute_adaptive_target(
    config: CalorieTargetConfig,
    today_active_cal: int,
    prev_7d_active_cals: list[int],
    yesterday_consumed: int | None,
    yesterday_target: int | None,
    tomorrow_has_long_run: bool,
) -> int:
    """Compute the adaptive calorie target for a single day.

    All DB access happens outside this function — it receives pre-fetched data.
    """
    base = config.sedentary - config.deficit

    # Factor 2: smoothed exercise add-back
    avg_7d = (
        sum(prev_7d_active_cals) / len(prev_7d_active_cals)
        if prev_7d_active_cals
        else 0
    )
    exercise_adj = (
        config.exercise_today_weight * today_active_cal
        + config.exercise_avg_weight * avg_7d
    )

    # Factor 3: yesterday's excess/deficit carry-over
    excess_adj = 0.0
    if yesterday_consumed is not None and yesterday_target is not None:
        excess_adj = -config.excess_carryover * (yesterday_consumed - yesterday_target)

    # Factor 4: tomorrow pre-load
    preload_adj = config.preload_bonus if tomorrow_has_long_run else 0

    target = base + exercise_adj + excess_adj + preload_adj
    return max(config.floor, round(target))


def load_calorie_config(db: Session) -> CalorieTargetConfig:
    """Load calorie target config from user_goals, falling back to defaults."""
    goals = (
        db.query(UserGoal)
        .filter(UserGoal.category == "calorie_target")
        .all()
    )
    overrides = {g.metric_key: g.target_value for g in goals}
    defaults = CalorieTargetConfig()
    return CalorieTargetConfig(
        sedentary=int(overrides.get("sedentary_calories", defaults.sedentary)),
        deficit=int(overrides.get("calorie_deficit", defaults.deficit)),
        exercise_today_weight=overrides.get("exercise_today_weight", defaults.exercise_today_weight),
        exercise_avg_weight=overrides.get("exercise_avg_weight", defaults.exercise_avg_weight),
        excess_carryover=overrides.get("excess_carryover", defaults.excess_carryover),
        preload_bonus=int(overrides.get("preload_bonus", defaults.preload_bonus)),
        preload_threshold_sec=int(overrides.get("preload_threshold_sec", defaults.preload_threshold_sec)),
        floor=int(overrides.get("calorie_floor", defaults.floor)),
    )


def compute_adaptive_targets_batch(
    config: CalorieTargetConfig,
    dates: list[date],
    active_cals: dict[date, int],
    consumed: dict[date, int],
    long_run_dates: set[date],
) -> dict[date, int]:
    """Compute adaptive targets for a list of dates, chaining excess carry-over."""
    results: dict[date, int] = {}
    prev_target: int | None = None

    for d in sorted(dates):
        today_active = active_cals.get(d, 0)
        prev_7d = [
            active_cals.get(d - timedelta(days=i), 0)
            for i in range(1, 8)
        ]

        yesterday = d - timedelta(days=1)
        yesterday_consumed = consumed.get(yesterday)
        yesterday_target = prev_target  # from previous iteration

        tomorrow = d + timedelta(days=1)
        tomorrow_long = tomorrow in long_run_dates

        target = compute_adaptive_target(
            config=config,
            today_active_cal=today_active,
            prev_7d_active_cals=prev_7d,
            yesterday_consumed=yesterday_consumed,
            yesterday_target=yesterday_target,
            tomorrow_has_long_run=tomorrow_long,
        )
        results[d] = target
        prev_target = target

    return results


def fetch_and_compute_targets(
    db: Session,
    from_date: date,
    to_date: date,
) -> dict[date, int]:
    """Fetch all needed data from DB and compute adaptive targets for a date range."""
    config = load_calorie_config(db)

    # Batch-fetch active calories: [from_date - 7 .. to_date]
    cal_start = from_date - timedelta(days=7)
    daily_rows = (
        db.query(DailySummary.date, DailySummary.calories_active)
        .filter(DailySummary.date >= cal_start, DailySummary.date <= to_date)
        .all()
    )
    active_cals = {r.date: r.calories_active or 0 for r in daily_rows}

    # Batch-fetch consumed: [from_date - 1 .. to_date]
    nutr_rows = (
        db.query(NutritionDaily.date, NutritionDaily.calories)
        .filter(NutritionDaily.date >= from_date - timedelta(days=1), NutritionDaily.date <= to_date)
        .all()
    )
    consumed = {r.date: r.calories for r in nutr_rows if r.calories is not None}

    # Batch-fetch planned long runs: [from_date .. to_date + 1]
    planned_rows = (
        db.query(TPPlannedWorkout.date)
        .filter(
            TPPlannedWorkout.date >= from_date,
            TPPlannedWorkout.date <= to_date + timedelta(days=1),
            TPPlannedWorkout.duration_sec_planned > config.preload_threshold_sec,
        )
        .all()
    )
    long_run_dates = {r.date for r in planned_rows}

    # Build date list
    days = []
    d = from_date
    while d <= to_date:
        days.append(d)
        d += timedelta(days=1)

    return compute_adaptive_targets_batch(config, days, active_cals, consumed, long_run_dates)
