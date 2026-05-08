from datetime import date, time

from app.coach.rules import wake_time


def test_weekend_returns_0830():
    saturday = date(2026, 5, 9)
    assert wake_time.compute(saturday, {"type": "run", "duration_min": 60}) == time(8, 30)
    sunday = date(2026, 5, 10)
    assert wake_time.compute(sunday, None) == time(8, 30)


def test_weekday_rest():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, None) == time(7, 15)


def test_weekday_strength_only():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "strength"}) == time(6, 15)


def test_weekday_run_60():
    monday = date(2026, 5, 11)
    # end 8:00 - 60 - 20 = 6:40
    assert wake_time.compute(monday, {"type": "run", "duration_min": 60}) == time(6, 40)


def test_weekday_run_75():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "run", "duration_min": 75}) == time(6, 25)


def test_weekday_run_90():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "run", "duration_min": 90}) == time(6, 10)


def test_weekday_run_45():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "run", "duration_min": 45}) == time(6, 55)


def test_weekday_run_120():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "run", "duration_min": 120}) == time(5, 40)


def test_weekday_cross_outdoor_75():
    monday = date(2026, 5, 11)
    assert wake_time.compute(monday, {"type": "bike", "duration_min": 75}) == time(6, 25)


def test_mixed_with_outdoor_primary():
    monday = date(2026, 5, 11)
    sessions = [{"type": "run", "duration_min": 60}, {"type": "strength"}]
    assert wake_time.compute(monday, {"sessions": sessions}) == time(6, 40)


def test_mixed_strength_only_fallback():
    monday = date(2026, 5, 11)
    sessions = [{"type": "strength"}, {"type": "yoga"}]
    # has unknown + strength -> not mixed by category, treated as strength_only
    cat = "computed elsewhere"  # documents intent
    _ = cat
    assert wake_time.compute(monday, {"sessions": sessions}) == time(6, 15)


def test_unknown_type_defaults_to_run():
    monday = date(2026, 5, 11)
    # unknown + duration -> classified as run, end_anchor - 30 - 20 = 7:10
    assert wake_time.compute(monday, {"type": "swim", "duration_min": 30}) == time(7, 10)
