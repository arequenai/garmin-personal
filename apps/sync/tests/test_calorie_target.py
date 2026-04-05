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
