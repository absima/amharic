from am_normalizer.normalize import normalize

def test_i_as_no_vowel_habit_alternative():
    out = normalize("migib", {"latin_mode": "auto", "return_alternatives": True, "max_alternatives": 5})
    assert out["text_am"] == "ሚጊብ"
    alts = [a["text_am"] for a in out.get("alternatives", [])]
    assert "ምግብ" in alts
