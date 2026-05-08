"""Dinner macros rule. Pure function."""
from __future__ import annotations


def compute(daily_targets: dict, consumed_today: dict, cfg: dict) -> dict:
    deficit_c = max(int(daily_targets["carb_g"]) - int(consumed_today.get("carb_g", 0) or 0), 0)
    deficit_p = max(int(daily_targets["prot_g"]) - int(consumed_today.get("prot_g", 0) or 0), 0)
    deficit_f = max(int(daily_targets["fat_g"]) - int(consumed_today.get("fat_g", 0) or 0), 0)

    dinner_c = min(deficit_c, int(cfg["dinner_carb_cap_g"]))
    dinner_p = min(deficit_p, int(cfg["dinner_protein_cap_g"]))
    dinner_f = min(deficit_f, 25)

    dinner_kcal = dinner_c * 4 + dinner_p * 4 + dinner_f * 9
    if dinner_kcal < 300:
        dinner_kcal = 300
        dinner_c = 15
        dinner_p = 35
        dinner_f = 12

    return {
        "kcal": int(round(dinner_kcal)),
        "c": int(dinner_c),
        "p": int(dinner_p),
        "g": int(dinner_f),
    }
