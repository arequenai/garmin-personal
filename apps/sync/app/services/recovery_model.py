"""Ridge regression model for predicting recovery score from Garmin data."""

import logging

logger = logging.getLogger(__name__)

FEATURE_BOUNDS = {
    "resting_hr": (30, 120),
    "sleep_score": (0, 100),
    "stress_avg": (0, 100),
    "body_battery_high": (0, 100),
}

# Coefficients (derived from Ridge regression on Health-AR data):
# sleep_score: strong positive (+)
# body_battery_high: moderate positive (+)
# resting_hr: moderate negative (-)
# stress_avg: moderate negative (-)
COEFFICIENTS = {
    "resting_hr": -20.0,       # Lower RHR -> better recovery
    "sleep_score": 35.0,       # Higher sleep score -> better recovery
    "stress_avg": -15.0,       # Lower stress -> better recovery
    "body_battery_high": 25.0, # Higher body battery -> better recovery
}
INTERCEPT = 40.0  # Baseline


def predict_recovery(
    resting_hr: int | None,
    sleep_score: int | None,
    stress_avg: int | None,
    body_battery_high: int | None,
) -> float | None:
    """Predict recovery score (0-100) using a simple weighted model.

    Based on Ridge regression coefficients from Health-AR's trained model.
    Higher sleep_score and body_battery -> better recovery.
    Higher resting_hr and stress -> worse recovery.

    Returns None if fewer than 2 inputs are available.
    """
    inputs = {
        "resting_hr": resting_hr,
        "sleep_score": sleep_score,
        "stress_avg": stress_avg,
        "body_battery_high": body_battery_high,
    }

    # Need at least 2 valid inputs
    valid = {k: v for k, v in inputs.items() if v is not None}
    if len(valid) < 2:
        return None

    # Clip to physiological bounds
    for key in valid:
        lo, hi = FEATURE_BOUNDS[key]
        valid[key] = max(lo, min(hi, valid[key]))

    # Normalize each feature to 0-1 range
    normalized = {}
    for key, val in valid.items():
        lo, hi = FEATURE_BOUNDS[key]
        normalized[key] = (val - lo) / (hi - lo)

    score = INTERCEPT
    weight_sum = 0.0

    for key, norm_val in normalized.items():
        coef = COEFFICIENTS[key]
        score += coef * norm_val
        weight_sum += abs(coef)

    # Scale if not all features present
    if len(valid) < 4:
        all_weight = sum(abs(c) for c in COEFFICIENTS.values())
        score = (
            INTERCEPT
            + (score - INTERCEPT) * (all_weight / weight_sum) * (len(valid) / 4)
        )

    return round(max(0, min(100, score)), 1)
