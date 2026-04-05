from app.services.calorie_target import compute_adaptive_target, CalorieTargetConfig


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
