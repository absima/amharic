from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class CarToken:
    base: str
    variant: Optional[str]  # "1" or "2" or None
    order: str              # "1".."8"


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
        if not s[i].isalpha():
            break

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


ORDER_TO_LATIN = {
    "1": "e",
    "2": "u",
    "3": "i",
    "4": "a",
    "5": "ei",  # order-5
    "6": "",    # no vowel
    "7": "o",
    "8": "oa",  # order-8 labialized
}

A_ORDER_TO_CARRIER = {
    "1": "_a",   # አ
    "2": "_u",   # ኡ
    "3": "_i",   # ኢ
    "4": "_aa",  # ኣ
    "5": "_ei",  # ኤ
    "6": "_",    # እ
    "7": "_o",   # ኦ
}

BASE_TO_LATIN_STD = {
    "kh":  "kx",   # ኸ
    "ny":  "nx",   # ኘ
    "zh":  "zx",   # ዠ
    "ts'": "cx",   # ጸ
    "p'":  "px",   # ጰ
    "t'":  "tx",   # ጠ
    "ch'": "chx",  # ጨ
    "sh":  "shx",  # ሽ
    # "ch" remains "ch"
}


ETH_TO_ASCII_PUNCT = {
    "፡": " ",
    "።": ".",
    "፣": ",",
    "፤": ";",
    "፥": ":",
    "፦": "::",
}


def ethiopic_punct_to_ascii(s: str) -> str:
    return "".join(ETH_TO_ASCII_PUNCT.get(ch, ch) for ch in (s or ""))


def car_to_latin_std(car: str) -> str:

    parts: List[str] = []

    chunks = re.findall(r"[A-Za-z'0-9]+|[^A-Za-z'0-9]+", car)

    for chunk in chunks:
        if not re.fullmatch(r"[A-Za-z'0-9]+", chunk):
            parts.append(chunk)
            continue

        lead_quotes = ""
        trail_quotes = ""
        while len(chunk) >= 2 and chunk[0] == "'" and chunk[1].isalpha():
            lead_quotes += "'"
            chunk = chunk[1:]
        while len(chunk) >= 2 and chunk[-1] == "'" and chunk[-2].isalnum():
            trail_quotes = "'" + trail_quotes
            chunk = chunk[:-1]

        if (not re.match(r"[A-Za-z]", chunk)) or (re.search(r"[A-Za-z]", chunk) is None):
            parts.append(lead_quotes + chunk + trail_quotes)
            continue

        tokens, idx = parse_car_prefix(chunk)
        if not tokens:
            parts.append(lead_quotes + chunk + trail_quotes)
            continue

        rest = chunk[idx:]  # payload: digits, etc.

        if lead_quotes:
            parts.append(lead_quotes)

        for t in tokens:
            # a-family
            if t.base == "a" and not t.variant:
                carrier = A_ORDER_TO_CARRIER.get(t.order)
                if carrier is None:
                    raise ValueError(f"Unsupported a-family order: a{t.order}")
                parts.append(carrier)
                continue


            if t.base == "h" and t.variant == "1":
                base_render = "hxx"
                vowel = ORDER_TO_LATIN[t.order]
                parts.append(base_render + vowel)
                continue
            if t.base == "h" and t.variant == "2":
                base_render = "hxxx"
                vowel = ORDER_TO_LATIN[t.order]
                parts.append(base_render + vowel)
                continue
            if t.base == "s" and t.variant == "1":
                base_render = "sx"   # ሠ-family
                vowel = ORDER_TO_LATIN[t.order]
                parts.append(base_render + vowel)
                continue
            if t.base == "ts'" and t.variant == "1":
                base_render = "cxx"  # ፀ-family (variant of ጸ in your tables)
                vowel = ORDER_TO_LATIN[t.order]
                parts.append(base_render + vowel)
                continue
            if t.base == "a" and t.variant == "1":
                base_render = "ax"   # ዐ-family
                vowel = ORDER_TO_LATIN[t.order]
                parts.append(base_render + vowel)
                continue

            base_render = BASE_TO_LATIN_STD.get(t.base, t.base)
            vowel = ORDER_TO_LATIN.get(t.order)
            if vowel is None:
                raise ValueError(f"Unsupported order: {t.order}")
            parts.append(base_render + vowel)

        if rest:
            parts.append(rest)
        if trail_quotes:
            parts.append(trail_quotes)

    return "".join(parts)


if __name__ == "__main__":
    from .normalize import load_car_maps

    car_to_am, am_to_car = load_car_maps()

    for ch in ["ሠ", "ሰ", "ዐ", "አ", "ፀ", "ጸ", "ሏ"]:
        car = am_to_car.get(ch)
        if car:
            print(ch, "->", car, "->", car_to_latin_std(car))
        else:
            print(ch, "not found in CAR table")
