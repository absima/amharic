from am_normalizer.latin_std import car_to_latin_std  # type: ignore  # noqa: E402


def test_car_to_latin_std_tarfaleh():
    assert car_to_latin_std("t4r6f4l1h6") == "tarfaleh"


def test_car_to_latin_std_vowel_carriers():
    # እ
    assert car_to_latin_std("a6") == "E"
    # ኤ
    assert car_to_latin_std("a5") == "EE"
    # አ
    assert car_to_latin_std("a1") == "A"


def test_car_to_latin_std_order5_operator():
    # h5 = ሄ -> hEi
    assert car_to_latin_std("h5") == "hEi"
