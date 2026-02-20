import json
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
ALIASES_PATH = ROOT / "resources" / "am_ui_aliases_v1.json"


def canon_alias(s: str) -> str:
    """
    Canonicalize alias input deterministically:
    - strip leading/trailing whitespace
    - lowercase
    - collapse internal whitespace to single spaces
    """
    s = s.strip().lower()
    s = " ".join(s.split())
    return s


def load_alias_map() -> Dict[str, str]:
    """
    Returns a map: canonical_alias -> ui_key
    """
    doc = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    if doc.get("version") != "am-ui-aliases-v1":
        raise ValueError(f"Unexpected aliases version: {doc.get('version')}")

    m: Dict[str, str] = {}
    for it in doc.get("items", []):
        alias = it.get("alias")
        key = it.get("key")
        if not isinstance(alias, str) or not isinstance(key, str):
            continue
        ca = canon_alias(alias)
        if not ca:
            continue
        if ca in m and m[ca] != key:
            raise ValueError(f"Alias collision: {alias!r} maps to both {m[ca]!r} and {key!r}")
        m[ca] = key
    return m
