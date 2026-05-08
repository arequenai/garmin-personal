from app.coach.rules import semaphore


def test_all_good_green():
    assert semaphore.compute(60, 60, 7.5, -10) == "green"


def test_one_bad_amber_low_hrv():
    # hrv 50 vs baseline 60 -> -10 < -5 -> +1
    assert semaphore.compute(50, 60, 7.5, -10) == "amber"


def test_one_bad_amber_short_sleep():
    assert semaphore.compute(60, 60, 6.0, -10) == "amber"


def test_one_bad_amber_low_tsb():
    assert semaphore.compute(60, 60, 7.5, -25) == "amber"


def test_two_bad_red():
    assert semaphore.compute(50, 60, 6.0, -10) == "red"


def test_three_bad_red():
    assert semaphore.compute(50, 60, 6.0, -25) == "red"


def test_missing_data_doesnt_crash():
    assert semaphore.compute(None, None, None, None) == "green"


def test_hrv_at_threshold_not_flagged():
    # baseline - 5 is the threshold, must be strictly less to flag
    assert semaphore.compute(55, 60, 7.5, -10) == "green"


def test_sleep_at_threshold_not_flagged():
    assert semaphore.compute(60, 60, 6.5, -10) == "green"


def test_tsb_at_threshold_not_flagged():
    assert semaphore.compute(60, 60, 7.5, -20) == "green"
