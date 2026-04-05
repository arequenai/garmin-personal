from dataclasses import dataclass


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
