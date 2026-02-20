from am_normalizer.normalize import normalize
from am_normalizer.latin_std import car_to_latin_std  # type: ignore  # noqa: E402


def test_sh_vs_s_plus_h_are_distinct():
    out1 = normalize("ታርፊያለሽ", {"latin_mode": "auto"})
    out2 = normalize("ታርፊያለስህ", {"latin_mode": "auto"})

    lat1 = car_to_latin_std(out1["car"])
    lat2 = car_to_latin_std(out2["car"])

    assert lat1 != lat2
    assert lat1.endswith("Sh")  # ሽ -> Sh (single base)
