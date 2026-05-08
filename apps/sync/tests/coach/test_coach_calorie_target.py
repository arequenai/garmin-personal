from app.coach.config import DEFAULTS
from app.coach.rules import calorie_target as ct


def test_base_returns_base():
    assert ct.compute(None, None, DEFAULTS) == DEFAULTS["base_kcal"]


def test_strength_tomorrow_adds_100():
    assert ct.compute(None, {"type": "strength"}, DEFAULTS) == DEFAULTS["base_kcal"] + 100


def test_z1_long_tomorrow_adds_200():
    w = {"type": "run", "description": "Z1 easy", "duration_min": 100}
    assert ct.compute(None, w, DEFAULTS) == DEFAULTS["base_kcal"] + 200


def test_quality_tomorrow_adds_300():
    w = {"type": "run", "description": "6x1k intervals", "duration_min": 60}
    assert ct.compute(None, w, DEFAULTS) == DEFAULTS["base_kcal"] + 300


def test_today_long_or_quality_adds_200():
    today = {"type": "run", "description": "Z1 easy", "duration_min": 120}
    assert ct.compute(today, None, DEFAULTS) == DEFAULTS["base_kcal"] + 200


def test_capped_at_plus_400():
    today = {"type": "run", "description": "intervals", "duration_min": 60}
    tomorrow = {
        "sessions": [
            {"type": "strength"},
            {"type": "run", "description": "intervals", "duration_min": 60},
            {"type": "run", "description": "Z1 easy", "duration_min": 100},
        ]
    }
    # would be base + 100 + 200 + 300 + 200 = +800, capped to +400
    assert ct.compute(today, tomorrow, DEFAULTS) == DEFAULTS["base_kcal"] + 400


def test_non_default_base_shifts():
    cfg = dict(DEFAULTS)
    cfg["base_kcal"] = 2200
    assert ct.compute(None, {"type": "strength"}, cfg) == 2300
