from datetime import time

from app.coach.config import DEFAULTS
from app.coach.rules import bedtime


def test_wake_615_default_cfg():
    # 6:15 - 7.5h - 20m = 22:25
    assert bedtime.compute(time(6, 15), DEFAULTS) == time(22, 25)


def test_wake_830_default_cfg():
    # 8:30 - 7.5h - 20m = 0:40
    assert bedtime.compute(time(8, 30), DEFAULTS) == time(0, 40)


def test_wake_640_default_cfg():
    # 6:40 - 7.5h - 20m = 22:50
    assert bedtime.compute(time(6, 40), DEFAULTS) == time(22, 50)


def test_non_default_target_sleep_hours_shifts():
    cfg = dict(DEFAULTS)
    cfg["target_sleep_hours"] = 8.0  # +30m more sleep
    # 6:40 - 8h - 20m = 22:20
    assert bedtime.compute(time(6, 40), cfg) == time(22, 20)


def test_non_default_latency_shifts():
    cfg = dict(DEFAULTS)
    cfg["sleep_latency_min"] = 10
    # 6:15 - 7.5h - 10m = 22:35
    assert bedtime.compute(time(6, 15), cfg) == time(22, 35)
