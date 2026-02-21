import json
from am_normalizer.normalize import normalize  
from am_normalizer.paths import data_path

LEXICON = data_path("resources", "am_ui_v1.json")


def test_ui_lexicon_roundtrip_and_confidence():
    lex = json.loads(LEXICON.read_text(encoding="utf-8"))
    assert lex["version"] == "am-ui-v1"

    # Guard against accidental key collisions
    keys = [i["key"] for i in lex["items"]]
    assert len(keys) == len(set(keys)), "Duplicate keys in lexicon"

    for item in lex["items"]:
        key = item["key"]
        am = item["am"]

        out = normalize(am, {"latin_mode": "auto"})

        # Ethiopic UI strings must round-trip exactly
        assert out["text_am"] == am, key

        # Ethiopic-only inputs should be very confident (tune if needed)
        assert out["confidence"] >= 0.98, key

        # CAR must be pinned and match exactly
        assert "car" in item and isinstance(item["car"], str) and item["car"], key
        assert out["car"] == item["car"], key


