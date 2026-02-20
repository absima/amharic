#!/usr/bin/env python3
import json
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEXICON_PATH = ROOT / "resources" / "am_ui_v1.json"

from am_normalizer.normalize import normalize  # type: ignore  # noqa: E402


def main() -> int:
    lex = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
    if lex.get("version") != "am-ui-v1":
        print(f"Unexpected lexicon version: {lex.get('version')}", file=sys.stderr)
        return 2

    updated = deepcopy(lex)
    changed = 0

    for item in updated["items"]:
        key = item["key"]
        am = item["am"]

        out = normalize(am, {"latin_mode": "auto"})
        car = out.get("car")

        if not isinstance(car, str) or not car:
            raise RuntimeError(f"Missing/invalid car for {key}: {out}")

        # Optional safety: ensure round-trip exact for Ethiopic
        if out.get("text_am") != am:
            raise RuntimeError(f"text_am mismatch for {key}: {am} vs {out.get('text_am')}")

        old = item.get("car")
        if old != car:
            item["car"] = car
            changed += 1

    # Write a pinned output next to the original for review
    out_path = LEXICON_PATH.with_suffix(".pinned.json")
    out_path.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Wrote: {out_path}")
    print(f"Items updated/filled: {changed}/{len(updated['items'])}")
    print("Review the diff, then replace am_ui_v1.json if it looks correct.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

