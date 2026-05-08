from app.coach.config import DEFAULTS
from app.coach.rules import dinner_macros


def test_normal_day_uses_deficits():
    daily = {"prot_g": 150, "carb_g": 300, "fat_g": 80}
    consumed = {"prot_g": 100, "carb_g": 220, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, DEFAULTS)
    # deficits: 50 P, 80 C, 20 F (under caps)
    assert out["p"] == 50
    assert out["c"] == 80
    assert out["g"] == 20


def test_caps_dinner_carbs():
    daily = {"prot_g": 150, "carb_g": 400, "fat_g": 80}
    consumed = {"prot_g": 100, "carb_g": 50, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, DEFAULTS)
    assert out["c"] == DEFAULTS["dinner_carb_cap_g"]


def test_caps_dinner_protein():
    daily = {"prot_g": 200, "carb_g": 200, "fat_g": 80}
    consumed = {"prot_g": 50, "carb_g": 150, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, DEFAULTS)
    assert out["p"] == DEFAULTS["dinner_protein_cap_g"]


def test_surplus_day_uses_floor():
    daily = {"prot_g": 100, "carb_g": 200, "fat_g": 60}
    consumed = {"prot_g": 100, "carb_g": 200, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, DEFAULTS)
    # all deficits zero -> kcal would be 0 -> floor to 300
    assert out["kcal"] == 300
    assert out["c"] == 15
    assert out["p"] == 35
    assert out["g"] == 12


def test_kcal_consistent_with_macros():
    daily = {"prot_g": 150, "carb_g": 300, "fat_g": 80}
    consumed = {"prot_g": 100, "carb_g": 220, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, DEFAULTS)
    expected = out["c"] * 4 + out["p"] * 4 + out["g"] * 9
    assert out["kcal"] == expected


def test_non_default_carb_cap_shifts():
    cfg = dict(DEFAULTS)
    cfg["dinner_carb_cap_g"] = 80
    daily = {"prot_g": 150, "carb_g": 400, "fat_g": 80}
    consumed = {"prot_g": 100, "carb_g": 50, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, cfg)
    assert out["c"] == 80


def test_non_default_protein_cap_shifts():
    cfg = dict(DEFAULTS)
    cfg["dinner_protein_cap_g"] = 40
    daily = {"prot_g": 200, "carb_g": 200, "fat_g": 80}
    consumed = {"prot_g": 50, "carb_g": 150, "fat_g": 60}
    out = dinner_macros.compute(daily, consumed, cfg)
    assert out["p"] == 40
