"""Training load and recovery calculation functions.

Pure calculation functions used by SyncService (TSS per activity)
and PerformanceUpdater (daily ATL/CTL/TSB).
"""


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
    """Exponentially weighted moving average for CTL (42d) or ATL (7d)."""
    if not tss_values:
        return 0.0
    decay = 2.0 / (days + 1)
    ewma = 0.0
    for tss in tss_values:
        ewma = tss * decay + ewma * (1 - decay)
    return round(ewma, 2)


def calculate_tsb(ctl: float, atl: float) -> float:
    """Training Stress Balance = CTL - ATL."""
    return round(ctl - atl, 2)


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
