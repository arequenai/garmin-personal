from app.coach.config import DEFAULTS
from app.coach.rules import macro_split


def test_default_protein_constant():
    out = macro_split.compute(2400, None, DEFAULTS)
    # 1.8 * 75 = 135
    assert out["prot_g"] == 135


def test_carbs_4_per_kg_when_easy():
    out = macro_split.compute(2400, None, DEFAULTS)
    # 4 * 75 = 300
    assert out["carb_g"] == 300


def test_carbs_5_per_kg_when_strength():
    out = macro_split.compute(2400, {"type": "strength"}, DEFAULTS)
    assert out["carb_g"] == 5 * 75


def test_carbs_6_per_kg_when_quality():
    w = {"type": "run", "description": "6x1k intervals"}
    out = macro_split.compute(2400, w, DEFAULTS)
    assert out["carb_g"] == 6 * 75


def test_fat_floor_600_kcal():
    # huge protein + carb -> fat floor at 600 kcal => 67g
    out = macro_split.compute(1500, None, DEFAULTS)
    # prot_kcal = 540, carb_kcal = 1200 -> total 1740, would imply -240 fat -> floored
    assert out["fat_g"] == round(600 / 9)


def test_non_default_body_weight_shifts():
    cfg = dict(DEFAULTS)
    cfg["body_weight_kg"] = 80
    out = macro_split.compute(2400, None, cfg)
    assert out["prot_g"] == round(1.8 * 80)
    assert out["carb_g"] == 4 * 80


def test_non_default_protein_per_kg_shifts():
    cfg = dict(DEFAULTS)
    cfg["protein_g_per_kg"] = 2.2
    out = macro_split.compute(2400, None, cfg)
    assert out["prot_g"] == round(2.2 * 75)
