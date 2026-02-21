"""
Validator for AN-v0 normalization tests.

Expects tests/normalize.json with entries like:
- in
- expect_text_am (optional)
- expect_has_alternatives (optional bool)
"""

from __future__ import annotations
import json
from pathlib import Path
from am_normalizer.normalize import normalize  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"

# Import normalize.py without packaging


def main():
    path = TESTS / "normalize.json"
    if not path.exists():
        raise SystemExit(f"Missing {path}")
    if path.stat().st_size == 0:
        raise SystemExit(f"{path} is empty")

    cases = json.loads(path.read_text(encoding="utf-8"))
    for i, case in enumerate(cases):
        inp = case["in"]
        # res = normalize(inp)
        res = normalize(inp, case.get("options"))

        if "expect_text_am" in case:
            exp = case["expect_text_am"]
            if res["text_am"] != exp:
                raise AssertionError(f"case[{i}] text_am mismatch: expected {exp!r} got {res['text_am']!r}")

        if case.get("expect_has_alternatives") is True:
            if not res.get("alternatives"):
                raise AssertionError(f"case[{i}] expected alternatives but got none")

        if case.get("expect_has_alternatives") is False:
            if res.get("alternatives"):
                raise AssertionError(f"case[{i}] expected no alternatives but got some")

        # Basic sanity: confidence range
        c = res.get("confidence", -1)
        if not (0.0 <= c <= 1.0):
            raise AssertionError(f"case[{i}] confidence out of range: {c}")

    print("OK: normalize.json validated.")


if __name__ == "__main__":
    main()

