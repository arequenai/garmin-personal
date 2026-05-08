"""Macro split rule. Pure function."""
from __future__ import annotations

from typing import Any

from app.coach import classifier


def compute(target_kcal: int, tomorrow_workout: Any, cfg: dict) -> dict:
    body_weight = float(cfg["body_weight_kg"])
    prot_per_kg = float(cfg["protein_g_per_kg"])

    prot_g = round(prot_per_kg * body_weight)

    if classifier.has_quality(tomorrow_workout) or classifier.has_z1_long(tomorrow_workout, 90):
        carb_g_per_kg = 6
    elif classifier.has_strength(tomorrow_workout):
        carb_g_per_kg = 5
    else:
        carb_g_per_kg = 4
    carb_g = round(carb_g_per_kg * body_weight)

    prot_kcal = prot_g * 4
    carb_kcal = carb_g * 4
    fat_kcal = max(int(target_kcal) - prot_kcal - carb_kcal, 600)
    fat_g = round(fat_kcal / 9)

    return {"prot_g": int(prot_g), "carb_g": int(carb_g), "fat_g": int(fat_g)}
