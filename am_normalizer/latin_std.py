# tools/latin_std.py
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CarToken:
    base: str
    variant: Optional[str]  # "1" or "2" or None
    order: str              # "1".."8"


def parse_car_stream(s: str) -> List[CarToken]:
    """
    Parse delimiterless CAR stream into tokens.
    Token pattern: <base><variant?><order>
      - base: [a-z]+ optionally containing "'"
      - variant: optional [1-2]
      - order: [1-8]

    IMPORTANT:
    We cannot finalize a token at the first digit because variant digits (1/2)
    may appear before the order digit.
    """
    tokens: List[CarToken] = []
    i = 0

    while i < len(s):
        # read base (letters and apostrophe)
        j = i
        while j < len(s) and (s[j].isalpha() or s[j] == "'"):
            j += 1
        if j == i:
            raise ValueError(f"Invalid CAR stream at {i}: expected base, got {s[i]!r}")

        base = s[i:j]
        if j >= len(s) or not s[j].isdigit():
            raise ValueError(f"Invalid CAR token at {i}: missing order digit after base {base!r}")

        variant: Optional[str] = None

        # If there are TWO digits available, interpret as variant+order.
        # Else ONE digit is order only.
        if j + 1 < len(s) and s[j] in "12" and s[j + 1] in "12345678":
            variant = s[j]
            order = s[j + 1]
            i = j + 2
        else:
            order = s[j]
            i = j + 1

        tokens.append(CarToken(base=base, variant=variant, order=order))

    return tokens

def parse_car_prefix(s: str) -> tuple[list[CarToken], int]:
    """
    Parse as many CAR tokens as possible from the start of s.
    Returns (tokens, index_after_last_token).
    If the next part cannot start a token (e.g., digit payload), stop cleanly.
    """
    tokens: list[CarToken] = []
    i = 0
    n = len(s)

    while i < n:
        # token must start with a letter (or apostrophe as part of base is only allowed after letters)
        if not s[i].isalpha():
            break

        # read base (letters + apostrophe)
        j = i
        while j < n and (s[j].isalpha() or s[j] == "'"):
            j += 1
        if j == i:
            break

        base = s[i:j]
        if j >= n or not s[j].isdigit():
            break

        variant: Optional[str] = None

        # variant+order (two digits)
        if j + 1 < n and s[j] in "12" and s[j + 1] in "12345678":
            variant = s[j]
            order = s[j + 1]
            i = j + 2
        # order only (one digit)
        elif s[j] in "12345678":
            order = s[j]
            i = j + 1
        else:
            break

        tokens.append(CarToken(base=base, variant=variant, order=order))

    return tokens, i

# CAR order -> Latin-Std vowel/operator (consonant families)
ORDER_TO_LATIN = {
    "1": "e",
    "2": "u",
    "3": "i",
    "4": "a",
    "5": "Ei",  # order-5 operator (locked)
    "6": "",    # no vowel
    "7": "o",
    "8": "Wa",  # locked convention for order-8
}

# Vowel carrier family (base "a") -> Latin-Std carrier tokens (locked)
A_ORDER_TO_CARRIER = {
    "1": "A",   # አ
    "2": "U",   # ኡ
    "3": "I",   # ኢ
    "4": "AA",  # ኣ
    "5": "EE",  # ኤ
    "6": "E",   # እ  (locked: E / EE / Ei precedence)
    "7": "O",   # ኦ
}

# Base -> Latin-Std rendering (deterministic).
# Priority: your single-letter explicit selectors, then any remaining disambiguators.
BASE_TO_LATIN_STD = {
    # --- single-letter explicit selectors (your standard) ---
    "kh":  "K",    # ኸ
    "ny":  "N",    # ኘ
    "zh":  "Z",    # ዠ
    "ts'": "X",    # ጸ  (variant1 handled specially -> Y for ፀ)

    "p'":  "P",    # ጰ
    "t'":  "T",    # ጠ
    "ch'": "C",    # ጨ
    "ch":  "c",    # ቸ

    # --- remaining disambiguator still needed ---
    "sh": "Sh",    # ሽ-family
}

ETH_TO_ASCII_PUNCT = {
    "፡": " ",
    "።": ".",
    "፣": ",",
    "፤": ";",
    "፥": ":",
    "፦": "::",  # policy choice
}

def ethiopic_punct_to_ascii(s: str) -> str:
    return "".join(ETH_TO_ASCII_PUNCT.get(ch, ch) for ch in (s or ""))

def car_to_latin_std(car: str) -> str:
    """
    Deterministic CAR -> Latin-Std rendering.

    Accepts mixed streams that may include whitespace / punctuation.
    We convert CAR tokens inside letter/apostrophe/digit runs, and pass the rest through.
    """
    parts: List[str] = []

    # Split into: [CAR-ish runs] or [everything else]
    chunks = re.findall(r"[A-Za-z'0-9]+|[^A-Za-z'0-9]+", car)

    for chunk in chunks:
        # Pass through non CAR-ish chunks (spaces, punctuation, etc.)
        if not re.fullmatch(r"[A-Za-z'0-9]+", chunk):
            parts.append(chunk)
            continue

        # Peel off leading/trailing single quotes used as quotation marks,
        # so they don't block CAR parsing (CAR bases never start/end with a bare quote).
        lead_quotes = ""
        trail_quotes = ""
        while len(chunk) >= 2 and chunk[0] == "'" and chunk[1].isalpha():
            lead_quotes += "'"
            chunk = chunk[1:]
        while len(chunk) >= 2 and chunk[-1] == "'" and chunk[-2].isalnum():
            trail_quotes = "'" + trail_quotes
            chunk = chunk[:-1]

        # Only attempt CAR parsing if this run starts with a letter and contains at least one letter.
        # Otherwise, treat as passthrough (e.g., list numbers).
        if (not re.match(r"[A-Za-z]", chunk)) or (re.search(r"[A-Za-z]", chunk) is None):
            parts.append(lead_quotes + chunk + trail_quotes)
            continue

        # Parse and render CAR tokens from this run
        # try:
        #     tokens = parse_car_stream(chunk)
        # except ValueError:
        #     # Not a valid CAR run (e.g., stray apostrophes). Pass through unchanged.
        #     parts.append(lead_quotes + chunk + trail_quotes)
        #     continue
        tokens, idx = parse_car_prefix(chunk)
        if not tokens:
            parts.append(lead_quotes + chunk + trail_quotes)
            continue

        rest = chunk[idx:]  # payload: digits, etc.

        if lead_quotes:
            parts.append(lead_quotes)

        for t in tokens:
            # vowel carriers (a-family)
            if t.base == "a":
                carrier = A_ORDER_TO_CARRIER.get(t.order)
                if carrier is None:
                    raise ValueError(f"Unsupported a-family order: a{t.order}")

                # If a-family has a variant, treat it as a distinct consonant family (e.g., ዐ)
                if t.variant:
                    base_render = "J"  # ዐ-family
                    vowel = ORDER_TO_LATIN.get(t.order)
                    if vowel is None:
                        raise ValueError(f"Unsupported order: {t.order}")
                    parts.append(base_render + vowel)
                else:
                    parts.append(carrier)
                continue

            # consonant families (variant-dependent overrides)
            if t.base == "h" and t.variant == "1":
                base_render, var_render = "H", ""
            elif t.base == "h" and t.variant == "2":
                base_render, var_render = "Q", ""
            elif t.base == "ts'" and t.variant == "1":
                base_render, var_render = "Y", ""
            elif t.base == "s" and t.variant == "1":
                base_render, var_render = "V", ""
            else:
                base_render = BASE_TO_LATIN_STD.get(t.base, t.base)
                var_render = t.variant or ""

            vowel = ORDER_TO_LATIN.get(t.order)
            if vowel is None:
                raise ValueError(f"Unsupported order: {t.order}")

            parts.append(base_render + var_render + vowel)
        if rest:
            parts.append(rest)
        if trail_quotes:
            parts.append(trail_quotes)

    return "".join(parts)


if __name__ == "__main__":
    from .normalize import load_car_maps

    car_to_am, am_to_car = load_car_maps()

    for ch in ["ሠ", "ሰ", "ዐ", "አ", "ፀ", "ጸ"]:
        car = am_to_car.get(ch)
        if car:
            print(ch, "->", car, "->", car_to_latin_std(car))
            # print(ch, "car repr:", repr(car), "chars:", [hex(ord(c)) for c in car])

        else:
            print(ch, "not found in CAR table")



