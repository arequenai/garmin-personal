from app.coach import classifier


def test_none_is_rest():
    assert classifier.classify_workout(None) == "rest"


def test_empty_is_rest():
    assert classifier.classify_workout({}) == "rest"
    assert classifier.classify_workout([]) == "rest"


def test_strength_only():
    assert classifier.classify_workout({"type": "strength"}) == "strength_only"
    assert classifier.classify_workout({"type": "Gym"}) == "strength_only"


def test_run():
    assert classifier.classify_workout({"type": "run", "duration_min": 60}) == "run"
    assert classifier.classify_workout({"type": "Trail"}) == "run"


def test_cross_outdoor():
    assert classifier.classify_workout({"type": "bike", "duration_min": 75}) == "cross_outdoor"
    assert classifier.classify_workout({"type": "MTB"}) == "cross_outdoor"


def test_mixed_run_plus_strength():
    sessions = [{"type": "run", "duration_min": 60}, {"type": "strength"}]
    assert classifier.classify_workout({"sessions": sessions}) == "mixed"


def test_unknown_defaults_to_run():
    assert classifier.classify_workout({"type": "scuba"}) == "run"


def test_has_quality_intervals():
    assert classifier.has_quality({"type": "run", "description": "6x1000 intervals"})


def test_has_quality_high_if():
    assert classifier.has_quality({"type": "run", "planned_if": 0.9})


def test_has_z1_long():
    assert classifier.has_z1_long({"type": "run", "description": "Z1 easy", "duration_min": 100})
    assert not classifier.has_z1_long({"type": "run", "description": "Z1", "duration_min": 60})


def test_has_strength():
    assert classifier.has_strength({"sessions": [{"type": "strength"}, {"type": "run"}]})
    assert not classifier.has_strength({"type": "run"})
