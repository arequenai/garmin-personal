from datetime import datetime

import pytest

from app.services.calculations import (
    calculate_ewma,
    calculate_recovery_score,
    calculate_stress_last_hour,
    calculate_tsb,
    calculate_tss_hr,
    calculate_tss_power,
    calculate_tss_strength,
)

# --- TSS Tests ---


def test_tss_hr_at_threshold():
    # 1 hour at threshold = 100 TSS
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=165, hr_threshold=165)
    assert tss == pytest.approx(100.0, rel=0.01)


def test_tss_hr_easy():
    # 1 hour at 75% of threshold
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=124, hr_threshold=165)
    assert tss < 60


def test_tss_hr_hard():
    # 1 hour above threshold
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=175, hr_threshold=165)
    assert tss > 100


def test_tss_hr_missing_data():
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=None, hr_threshold=165)
    assert tss is None


def test_tss_hr_zero_threshold():
    tss = calculate_tss_hr(duration_sec=3600, avg_hr=150, hr_threshold=0)
    assert tss is None


def test_tss_power_at_ftp():
    # 1 hour at FTP = 100 TSS
    tss = calculate_tss_power(duration_sec=3600, normalized_power=250, ftp=250)
    assert tss == pytest.approx(100.0, rel=0.01)


def test_tss_power_missing():
    tss = calculate_tss_power(duration_sec=3600, normalized_power=None, ftp=250)
    assert tss is None


def test_tss_strength():
    tss = calculate_tss_strength(duration_sec=3600, training_effect=3.5)
    assert tss > 0
    assert tss < 200


def test_tss_strength_missing():
    tss = calculate_tss_strength(duration_sec=3600, training_effect=None)
    assert tss is None


# --- EWMA Tests ---


def test_ewma_empty():
    result = calculate_ewma([], days=7)
    assert result == 0.0


def test_ewma_single():
    result = calculate_ewma([100.0], days=7)
    assert result > 0


def test_ctl_converges():
    # 42-day EWMA with constant 50 TSS should converge near 50
    tss_values = [50.0] * 120
    ctl = calculate_ewma(tss_values, days=42)
    assert ctl == pytest.approx(50.0, rel=0.05)


def test_atl_converges():
    # 7-day EWMA with constant 50 TSS should converge near 50
    tss_values = [50.0] * 14
    atl = calculate_ewma(tss_values, days=7)
    assert atl == pytest.approx(50.0, rel=0.05)


def test_ewma_responds_to_recent():
    # Recent high value should pull EWMA up
    tss_values = [10.0] * 20 + [100.0]
    result = calculate_ewma(tss_values, days=7)
    assert result > 10.0


# --- TSB Tests ---


def test_tsb_calculation():
    tsb = calculate_tsb(ctl=50.0, atl=70.0)
    assert tsb == -20.0


def test_tsb_positive():
    tsb = calculate_tsb(ctl=60.0, atl=40.0)
    assert tsb == 20.0


# --- Recovery Score Tests ---


def test_recovery_score_good():
    score = calculate_recovery_score(tsb=15.0, sleep_score=85, hrv=65.0)
    assert 60 <= score <= 100


def test_recovery_score_bad():
    score = calculate_recovery_score(tsb=-25.0, sleep_score=40, hrv=25.0)
    assert score < 50


def test_recovery_score_all_none():
    score = calculate_recovery_score(tsb=None, sleep_score=None, hrv=None)
    assert score == 50.0  # baseline


def test_recovery_score_clamped():
    # Extreme values should still be in 0-100
    score = calculate_recovery_score(tsb=100.0, sleep_score=100, hrv=200.0)
    assert 0 <= score <= 100
    score2 = calculate_recovery_score(tsb=-100.0, sleep_score=0, hrv=0.0)
    assert 0 <= score2 <= 100


# --- Stress Last Hour Tests ---


def test_stress_last_hour_basic():
    """Average stress from readings in the last 60 minutes."""
    now = datetime(2026, 4, 4, 14, 0, 0)
    readings = [
        # 50 min ago — included
        (datetime(2026, 4, 4, 13, 10, 0), 30),
        # 30 min ago — included
        (datetime(2026, 4, 4, 13, 30, 0), 40),
        # 10 min ago — included
        (datetime(2026, 4, 4, 13, 50, 0), 50),
        # 70 min ago — excluded
        (datetime(2026, 4, 4, 12, 50, 0), 90),
    ]
    result = calculate_stress_last_hour(readings, now)
    assert result == 40  # (30+40+50) / 3


def test_stress_last_hour_no_readings():
    now = datetime(2026, 4, 4, 14, 0, 0)
    result = calculate_stress_last_hour([], now)
    assert result is None


def test_stress_last_hour_skips_negative():
    """Negative values (-1=activity, -2=unusable) are excluded."""
    now = datetime(2026, 4, 4, 14, 0, 0)
    readings = [
        (datetime(2026, 4, 4, 13, 30, 0), 40),
        (datetime(2026, 4, 4, 13, 40, 0), -1),
        (datetime(2026, 4, 4, 13, 50, 0), 60),
    ]
    result = calculate_stress_last_hour(readings, now)
    assert result == 50  # (40+60) / 2
