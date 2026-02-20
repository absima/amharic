from am_normalizer.normalize import normalize

def test_sh_habit_is_alternative_in_auto():
    out = normalize("tarfiyalesh", {"latin_mode": "auto", "return_alternatives": True, "max_alternatives": 5})
    # one of these should be the best (depending on your scoring), but BOTH must appear across best+alts
    best = out["text_am"]
    alts = [a["text_am"] for a in out.get("alternatives", [])]
    assert ("ታርፊያለሽ" in [best] + alts)
    assert ("ታርፊያለስህ" in [best] + alts)
