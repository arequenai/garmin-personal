"""Category picker. Pure function."""
from __future__ import annotations

from typing import Any

from app.coach import classifier


def compute(dinner_macros: dict, tomorrow_workout: Any) -> dict:
    if classifier.has_quality(tomorrow_workout):
        carb_cat = "carb simple"
    elif classifier.has_strength(tomorrow_workout):
        carb_cat = "carb moderado"
    else:
        carb_cat = "carb complejo"

    return {
        "carb": carb_cat,
        "prot": "prot magra",
        "veg": "libre",
        "fat": "moderada",
    }
