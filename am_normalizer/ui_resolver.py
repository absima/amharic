
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .ui_aliases import load_alias_map, canon_alias

# Repo root (because resources/ is still at repo root for v0)
ROOT = Path(__file__).resolve().parents[1]

LEXICON_PATH = ROOT / "resources" / "am_ui_v1.json"
LEXICON = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))


CAR_TO_ITEM: Dict[str, Dict[str, Any]] = {item["car"]: item for item in LEXICON["items"]}
AM_TO_ITEM: Dict[str, Dict[str, Any]] = {item["am"]: item for item in LEXICON["items"]}
KEY_TO_ITEM: Dict[str, Dict[str, Any]] = {item["key"]: item for item in LEXICON["items"]}

ALIAS_TO_KEY: Dict[str, str] = load_alias_map()


def resolve_ui_key(text: str, *, latin_mode: str = "auto") -> Optional[Dict[str, Any]]:
    """
    Resolve user input to a pinned UI lexicon item.

    Resolution order:
      0) Direct key match (e.g., "ui.auth.login")
      1) Explicit alias match (canon_alias)
      2) normalize() -> text_am direct match
      3) normalize() -> exactly one alternative text_am match
      4) normalize() -> car match
    """
    s = (text or "").strip()
    if not s:
        return None

    # direct key match
    hit = KEY_TO_ITEM.get(s)
    if hit is not None:
        return hit

    # explicit aliases
    ca = canon_alias(s)
    key = ALIAS_TO_KEY.get(ca)
    if key is not None:
        return KEY_TO_ITEM.get(key)

    # Normalization pipeline
    from .normalize import normalize  # type: ignore

    out = normalize(s, {"latin_mode": latin_mode})

    am = out.get("text_am")
    if isinstance(am, str) and am in AM_TO_ITEM:
        return AM_TO_ITEM[am]

    alts = out.get("alternatives") or []
    matches = []
    for alt in alts:
        alt_am = alt.get("text_am")
        if isinstance(alt_am, str) and alt_am in AM_TO_ITEM:
            matches.append(AM_TO_ITEM[alt_am])
    if len(matches) == 1:
        return matches[0]

    car = out.get("car")
    if isinstance(car, str) and car in CAR_TO_ITEM:
        return CAR_TO_ITEM[car]

    return None
