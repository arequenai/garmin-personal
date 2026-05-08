from app.coach.rules import category_picker


def test_quality_tomorrow_simple_carb():
    out = category_picker.compute({}, {"type": "run", "description": "intervals"})
    assert out["carb"] == "carb simple"


def test_strength_tomorrow_moderado():
    out = category_picker.compute({}, {"type": "strength"})
    assert out["carb"] == "carb moderado"


def test_easy_or_rest_tomorrow_complejo():
    assert category_picker.compute({}, None)["carb"] == "carb complejo"
    out = category_picker.compute({}, {"type": "run", "duration_min": 45})
    assert out["carb"] == "carb complejo"


def test_static_categories():
    out = category_picker.compute({}, None)
    assert out["prot"] == "prot magra"
    assert out["veg"] == "libre"
    assert out["fat"] == "moderada"
