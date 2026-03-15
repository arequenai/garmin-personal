"""Training load and recovery calculation functions.

Pure calculation functions used by SyncService (TSS per activity)
and PerformanceUpdater (daily ATL/CTL/TSB).
"""

import math


def calculate_tss_hr(
    duration_sec: int,
    avg_hr: int | None,
    hr_threshold: int,
) -> float | None:
    """Calculate TSS from heart rate. 1 hour at threshold = 100 TSS."""
    if avg_hr is None or hr_threshold == 0:
        return None
    intensity_factor = avg_hr / hr_threshold
    tss = (duration_sec * intensity_factor**2 * 100) / 3600
    return round(tss, 1)


def calculate_tss_power(
    duration_sec: int,
    normalized_power: float | None,
    ftp: float,
) -> float | None:
    """Calculate TSS from power. 1 hour at FTP = 100 TSS."""
    if normalized_power is None or ftp == 0:
        return None
    intensity_factor = normalized_power / ftp
    tss = (duration_sec * normalized_power * intensity_factor) / (ftp * 36)
    return round(tss, 1)


def calculate_tss_strength(
    duration_sec: int,
    training_effect: float | None,
) -> float | None:
    """Estimate TSS for strength training based on duration and training effect.

    Linear scale: TE 1.0 ~ 20 TSS/hr, TE 5.0 ~ 120 TSS/hr.
    """
    if training_effect is None:
        return None
    tss_per_hour = 20 + (training_effect - 1.0) * 25
    tss = tss_per_hour * (duration_sec / 3600)
    return round(tss, 1)


def calculate_ewma(tss_values: list[float], days: int) -> float:
    """Exponentially weighted moving average for CTL (42d) or ATL (7d).

    Uses the physiological decay constant exp(-1/n), matching the
    TrainingPeaks / WKO standard used in sports science.
    """
    if not tss_values:
        return 0.0
    k = math.exp(-1.0 / days)
    ewma = 0.0
    for tss in tss_values:
        ewma = tss * (1 - k) + ewma * k
    return round(ewma, 2)


def calculate_tsb(ctl: float, atl: float) -> float:
    """Training Stress Balance = CTL - ATL."""
    return round(ctl - atl, 2)


def process_stress_data(stress_values: list[list]) -> dict:
    """Process raw Garmin stress data points with interpolation and smoothing.

    Args:
        stress_values: list of [timestamp_ms, stress_value] pairs.
            -1 = activity/missing, -2 = unusable

    Returns:
        dict with stress_avg, stress_max, stress_min, valid_readings
    """
    if not stress_values:
        return {
            "stress_avg": None,
            "stress_max": None,
            "stress_min": None,
            "valid_readings": 0,
        }

    import numpy as np

    # Extract values
    values = [v[1] for v in stress_values]

    # Replace -1 and -2 with NaN
    cleaned = [float(v) if v > 0 else float("nan") for v in values]

    if all(np.isnan(v) for v in cleaned):
        return {
            "stress_avg": None,
            "stress_max": None,
            "stress_min": None,
            "valid_readings": 0,
        }

    # Linear interpolation for short gaps (<=15 minutes = ~5 readings at 3min intervals)
    arr = np.array(cleaned)
    nans = np.isnan(arr)

    if nans.any() and not nans.all():
        valid_idx = np.where(~nans)[0]

        for i in range(len(valid_idx) - 1):
            start = valid_idx[i]
            end = valid_idx[i + 1]
            gap_size = end - start - 1

            # Only interpolate gaps of 5 or fewer points (~15 min)
            if 0 < gap_size <= 5:
                for j in range(1, gap_size + 1):
                    ratio = j / (gap_size + 1)
                    arr[start + j] = arr[start] * (1 - ratio) + arr[end] * ratio

    # Apply centered moving average (window=10)
    valid = arr[~np.isnan(arr)]
    if len(valid) >= 10:
        kernel = np.ones(10) / 10
        smoothed = np.convolve(valid, kernel, mode="valid")
        avg = float(np.mean(smoothed))
    else:
        avg = float(np.nanmean(arr))

    return {
        "stress_avg": round(avg),
        "stress_max": int(np.nanmax(valid)) if len(valid) > 0 else None,
        "stress_min": int(np.nanmin(valid)) if len(valid) > 0 else None,
        "valid_readings": int(len(valid)),
    }


def calculate_recovery_score(
    tsb: float | None,
    sleep_score: int | None,
    hrv: float | None,
) -> float:
    """Calculate recovery score (0-100) from TSB, sleep score, and HRV.

    Returns a baseline of 50.0 when all inputs are None.
    """
    weights = {"tsb": 0.35, "sleep": 0.40, "hrv": 0.25}
    score = 50.0  # baseline

    if tsb is not None:
        # TSB range typically -30 to +30, normalize to 0-100
        tsb_norm = max(0, min(100, (tsb + 30) / 60 * 100))
        score += (tsb_norm - 50) * weights["tsb"]

    if sleep_score is not None:
        score += (sleep_score - 50) * weights["sleep"]

    if hrv is not None:
        # HRV range typically 20-100, normalize to 0-100
        hrv_norm = max(0, min(100, (hrv - 20) / 80 * 100))
        score += (hrv_norm - 50) * weights["hrv"]

    return round(max(0, min(100, score)), 1)
