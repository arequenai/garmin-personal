from datetime import date, timedelta

from app.services.calorie_target import compute_adaptive_target, CalorieTargetConfig, compute_adaptive_targets_batch


def test_rest_day_returns_base():
    """No exercise today, no 7d history -> just base."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1500  # 1800 - 300


def test_exercise_today_adds_half():
    """600 cal exercise today, no 7d history -> base + 0.5*600 = 1800."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=600,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1800  # 1500 + 300


def test_exercise_7d_avg_adds_fraction():
    """No exercise today, 7d avg of 400 -> base + 0.3*400 = 1620."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[400, 400, 400, 400, 400, 400, 400],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1620  # 1500 + 120


def test_exercise_combined_today_and_avg():
    """800 cal today, 7d avg of 500 -> base + 0.5*800 + 0.3*500 = 2050."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=800,
        prev_7d_active_cals=[500, 500, 500, 500, 500, 500, 500],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 2050  # 1500 + 400 + 150


def test_excess_carryover_overate():
    """Overate 200 yesterday -> today -100."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=1700,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1400  # 1500 + 0 - 100 + 0


def test_excess_carryover_underate():
    """Underate 200 yesterday -> today +100."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=1300,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1600  # 1500 + 0 + 100 + 0


def test_excess_carryover_skipped_when_no_data():
    """Missing yesterday data -> no carry-over."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 1500


def test_preload_before_long_run():
    """Tomorrow has a long run -> +200."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=True,
    )
    assert result == 1700  # 1500 + 200


def test_floor_enforced():
    """Large overeating yesterday still can't push below floor."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=0,
        prev_7d_active_cals=[],
        yesterday_consumed=2500,
        yesterday_target=1500,
        tomorrow_has_long_run=False,
    )
    assert result == 1200  # floor; raw would be 1500 - 500 = 1000


def test_all_factors_combined():
    """All four factors active at once."""
    config = CalorieTargetConfig()
    result = compute_adaptive_target(
        config=config,
        today_active_cal=600,
        prev_7d_active_cals=[400, 400, 400, 400, 400, 400, 400],
        yesterday_consumed=1800,
        yesterday_target=1700,
        tomorrow_has_long_run=True,
    )
    # base=1500, ex=0.5*600+0.3*400=420, excess=-0.5*100=-50, preload=200
    assert result == 2070


def test_custom_config():
    """Custom config overrides defaults."""
    config = CalorieTargetConfig(sedentary=2000, deficit=200, exercise_today_weight=0.4)
    result = compute_adaptive_target(
        config=config,
        today_active_cal=500,
        prev_7d_active_cals=[],
        yesterday_consumed=None,
        yesterday_target=None,
        tomorrow_has_long_run=False,
    )
    assert result == 2000  # (2000-200) + 0.4*500 = 1800 + 200 = 2000


def test_batch_computes_iteratively():
    """Batch computes targets for a date range, chaining excess carry-over."""
    config = CalorieTargetConfig()
    base_date = date(2026, 3, 10)

    # active_cals: keyed by date
    active_cals = {
        base_date - timedelta(days=i): 300
        for i in range(1, 8)  # 7 days prior: all 300
    }
    active_cals[base_date] = 600  # day 1: exercise
    active_cals[base_date + timedelta(days=1)] = 0  # day 2: rest

    # consumed: day 1 overate by 200 vs expected target
    consumed = {base_date: 2200}

    # planned long runs: none
    long_run_dates: set[date] = set()

    dates = [base_date, base_date + timedelta(days=1)]
    results = compute_adaptive_targets_batch(
        config=config,
        dates=dates,
        active_cals=active_cals,
        consumed=consumed,
        long_run_dates=long_run_dates,
    )

    assert len(results) == 2
    # Day 1: base=1500, ex=0.5*600+0.3*300=390, excess=0 (no prev target), preload=0
    assert results[base_date] == 1890
    # Day 2: base=1500, ex=0.5*0+0.3*avg(300*6+600)/7=0.3*343~103,
    #   excess=-0.5*(2200-1890)=-155, preload=0
    #   = 1500+103-155 = 1448
    day2_prev7 = [300, 300, 300, 300, 300, 300, 600]
    day2_avg = sum(day2_prev7) / 7
    day2_ex = 0.5 * 0 + 0.3 * day2_avg
    day2_excess = -0.5 * (2200 - 1890)
    expected_day2 = max(1200, round(1500 + day2_ex + day2_excess))
    assert results[base_date + timedelta(days=1)] == expected_day2
