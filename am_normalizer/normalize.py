#!/usr/bin/env python3
"""
AN-v0 Normalizer (reference implementation)

- Uses CAR tables in tables/orders.tsv and tables/order8.tsv
- Stage A: segment scripts
- Stage B: Ethiopic normalization (whitespace + ፡ -> space)
- Stage C: Latin decoding (heuristic + ambiguity surfaced)
- Stage D/E: merge + final CAR encoding
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"


# Ethiopic basic block range (good enough for Amharic v0 work)
def is_ethiopic_char(ch: str) -> bool:
    o = ord(ch)
    return 0x1200 <= o <= 0x137F


def is_latin_char(ch: str) -> bool:
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch == "'"


def is_digit(ch: str) -> bool:
    return "0" <= ch <= "9"


def is_sep(ch: str) -> bool:
    return ch.isspace() or (not is_ethiopic_char(ch) and not is_latin_char(ch) and not is_digit(ch))


# ---- TSV helpers ----
def read_tsv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", encoding="utf-8") as f:
        header = None
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
                continue
            rows.append(dict(zip(header, parts)))
    return rows


def load_car_maps() -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    car_to_am: token -> char
    am_to_car: char -> token
    """
    car_to_am: Dict[str, str] = {}
    am_to_car: Dict[str, str] = {}

    def add_row(r: Dict[str, str]) -> None:
        base = r["base"]
        var = r.get("variant", "")
        order = r["order"]
        ch = r["char"]
        tok = f"{base}{var}{order}"
        car_to_am[tok] = ch
        am_to_car[ch] = tok

    for r in read_tsv(TABLES / "orders.tsv"):
        add_row(r)
    for r in read_tsv(TABLES / "order8.tsv"):
        add_row(r)

    return car_to_am, am_to_car

from functools import lru_cache

@lru_cache(maxsize=1)
def load_car_maps_cached() -> Tuple[Dict[str, str], Dict[str, str]]:
    return load_car_maps()

def _car_token_parts(tok: str) -> Tuple[str, Optional[str], str]:
    """
    Split a single CAR token like "ts'6" or "a16" or "zh27" into (base, variant, order).
    variant is "1"/"2" or None.
    """
    order = tok[-1]
    core = tok[:-1]
    variant = None
    if core and core[-1] in "12":
        variant = core[-1]
        base = core[:-1]
    else:
        base = core
    return base, variant, order

def _base_for_char(am_char: str) -> Tuple[str, Optional[str]]:
    """
    Return (base, forced_variant) for a given Ethiopic character using the TSV tables.
    forced_variant is only needed if the character lives in a variant family.
    """
    _, am_to_car = load_car_maps_cached()
    tok = am_to_car.get(am_char)
    if not tok:
        raise KeyError(f"Char not in tables: {am_char!r}")
    base, var, _ = _car_token_parts(tok)
    return base, var

# ---- Stage B: Ethiopic normalization (v0) ----
def normalize_ethiopic_text(s: str) -> str:
    s = s.replace("፡", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s
# --- punctuation mapping tables (v0) ---
ETH_TO_ASCII_PUNCT = {
    "፡": " ",   # word separator
    "።": ".",
    "፣": ",",
    "፤": ";",
    "፥": ":",
    "፦": "::",  # chosen policy; alternatively keep "፦"
}

ASCII_TO_ETH_PUNCT = {
    ",": "፣",
    ";": "፤",
}

# Abbrev tokens where '.' should be preserved (not converted to ።)
ABBREV_TOKENS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st",
    "etc", "eg", "ie", "vs", "am", "pm",
}

_CLOSERS = set(' \t\r\n")]}›»’”')  # treat '.' before these as sentence end


def ascii_punct_to_ethiopic(s: str) -> str:
    """
    Convert ASCII punctuation in Latin-input chunks to Ethiopic punctuation
    according to the v0 table, with a conservative "smart period" rule.

    - '::' -> ፦
    - ','  -> ፣
    - ';'  -> ፤
    - ':'  -> ፥  (but keep ':' in '://')
    - '.'  -> ።  only when it looks like a sentence end; keep '.' for abbreviations/decimals
    """
    if not s:
        return s

    # multi-char first
    s = s.replace("::", "፦")

    out = []
    i = 0
    n = len(s)

    def prev_alpha_token(idx: int) -> str:
        j = idx - 1
        while j >= 0 and s[j].isalpha():
            j -= 1
        return s[j + 1: idx].lower()

    def is_initialism_dot(idx: int) -> bool:
        # Detect patterns like U.S. or U.S.A. (at least "X." repeated)
        # Look left: "...X." and maybe earlier "Y."
        if idx < 1 or not s[idx - 1].isalpha():
            return False
        # look back for another ".<letter>." pattern nearby
        j = idx - 2
        while j >= 0 and s[j] in " \t":
            j -= 1
        # crude but effective: if we can find another letter-dot just before
        # e.g. "U.S." => at dot after S, we see "U." earlier
        return (j >= 1 and s[j] == "." and s[j - 1].isalpha())

    while i < n:
        ch = s[i]

        if ch in ASCII_TO_ETH_PUNCT:
            out.append(ASCII_TO_ETH_PUNCT[ch])
            i += 1
            continue

        if ch == ":":
            # keep : in URLs like http://, https://
            if i + 2 < n and s[i + 1] == "/" and s[i + 2] == "/":
                out.append(":")
            else:
                out.append("፥")
            i += 1
            continue

        if ch == ".":
            prev = s[i - 1] if i > 0 else ""
            nxt = s[i + 1] if i + 1 < n else ""

            # decimals: 3.14
            if prev.isdigit() and nxt.isdigit():
                out.append(".")
                i += 1
                continue

            # known abbrev token: Dr. etc. e.g. i.e.
            tok = prev_alpha_token(i)
            if tok in ABBREV_TOKENS:
                out.append(".")
                i += 1
                continue

            # initialisms: U.S. / U.S.A.
            if is_initialism_dot(i):
                out.append(".")
                i += 1
                continue

            # default: only convert to ። when it looks like sentence end
            # (end of string OR followed by whitespace/closer)
            if (i + 1 == n) or (nxt in _CLOSERS):
                out.append("።")
            else:
                out.append(".")
            i += 1
            continue

        out.append(ch)
        i += 1

    return "".join(out)

# ---- Stage A: segmentation ----
@dataclass
class Span:
    kind: str  # "ETH" | "LAT" | "NUM" | "SEP"
    text: str


def segment_scripts(s: str) -> List[Span]:
    spans: List[Span] = []
    if not s:
        return spans

    def base_kind(ch: str) -> str:
        if is_ethiopic_char(ch):
            return "ETH"
        if is_latin_char(ch):
            return "LAT"
        if is_digit(ch):
            return "NUM"
        return "SEP"

    def kind_at(i: int) -> str:
        ch = s[i]
        k = base_kind(ch)

        # # If this is a digit attached to Latin (e.g., s3m1t'4), treat as LAT
        # if k == "NUM":
        #     prev_is_lat = i > 0 and base_kind(s[i - 1]) == "LAT"
        #     next_is_lat = i + 1 < len(s) and base_kind(s[i + 1]) == "LAT"
        #     if prev_is_lat or next_is_lat:
        #         return "LAT"
        return k

    cur_kind = kind_at(0)
    buf = [s[0]]

    for i in range(1, len(s)):
        k = kind_at(i)
        if k == cur_kind:
            buf.append(s[i])
        else:
            spans.append(Span(cur_kind, "".join(buf)))
            cur_kind = k
            buf = [s[i]]

    spans.append(Span(cur_kind, "".join(buf)))
    return spans


# ---- Stage C: Latin decoding ----
BASES = [
    "ts'", "ch'", "p'", "t'",
    "sh", "ch", "ny", "zh", "kh",
    # singles
    "h", "l", "m", "r", "s", "q", "b", "t", "n", "k", "w", "z", "y", "d", "j", "g", "f", "p", "v", "a"
]

LAT_LEXICON = {
    "yet": "y1t6",   # የት
    "bota": "b7t4",  # ቦታ
    "mn": "m6n6",    # ምን
    "min": "m6n6",   # ምን
}

# Latin-Std explicit base selectors (single letters, case-sensitive)
# Note: user chose: c -> ch (ቸ), C -> ch' (ጨ), P -> p' (ጰ), T -> t' (ጠ)
STRICT_BASE_MAP = {
    "K": "kh",    # ኸ
    "N": "ny",    # ኘ
    "Z": "zh",    # ዠ
    "X": "ts'",   # ጸ
    "P": "p'",    # ጰ
    "T": "t'",    # ጠ
    "C": "ch'",   # ጨ
}

# --- derived strict selectors (do not guess; read from tables) ---
# We map the selector to either:
#   - a base string (normal), or
#   - a (base, forced_variant) tuple when needed.
STRICT_BASE_MAP_DERIVED = {}

# ሐ (ha variant), ኀ, ሠ, ፀ
for sel, ch in {
    "H": "ሐ",
    "Q": "ኀ",
    "R": "ሠ",
    "Y": "ፀ",
    "J": "ዐ",
}.items():
    base, var = _base_for_char(ch)
    STRICT_BASE_MAP_DERIVED[sel] = (base, var) if var else base

STRICT_BASE_MAP.update(STRICT_BASE_MAP_DERIVED)


CASE_DIGRAPHS = {
    "Sh": "sh", "SH": "sh",
    "Kh": "kh", "KH": "kh",
    "Ny": "ny", "NY": "ny",
    "Zh": "zh", "ZH": "zh",
    "Ch": "ch", "CH": "ch",
}

AUTO_DISABLED_BASES = {"sh", "kh", "ny", "zh", "ch"}

VOWEL_TO_ORDER = {
    "u": "2",
    "i": "3",
    "a": "4",
    "e": "1",
    "o": "7",
}

VOWEL2_TO_ORDER = {
    "ei": "5",
    }

# Latin-Std vowel-carrier tokens (case-sensitive) -> CAR tokens
LATIN_STD_CARRIERS = {
    "AA": "a4",  # ኣ
    "EE": "a5",  # ኤ
    "A":  "a1",  # አ
    "U":  "a2",  # ኡ
    "I":  "a3",  # ኢ
    "O":  "a7",  # ኦ
    "E":  "a6",  # እ  (locked: E / EE / Ei)
}

HABIT_DIGRAPH_BONUS = 0.75  # prior for lowercase 'sh' => ሽ (habit) vs s+h


@dataclass
class Candidate:
    car: str
    score: float
    reasons: List[str]


def try_decode_car_concatenation(word: str, car_to_am: Dict[str, str]) -> Optional[str]:
    i = 0
    out: List[str] = []
    while i < len(word):
        if word[i].isspace():
            out.append(word[i])
            i += 1
            continue
        if not (word[i].isalpha() or word[i] == "'"):
            return None

        j = i
        while j < len(word) and not word[j].isdigit():
            j += 1
        if j >= len(word):
            return None

        tok = None
        if j + 1 < len(word) and word[j].isdigit() and word[j + 1].isdigit():
            cand = word[i:j] + word[j] + word[j + 1]
            if cand in car_to_am:
                tok = cand
        if tok is None:
            cand = word[i:j] + word[j]
            if cand in car_to_am:
                tok = cand
        if tok is None:
            return None

        out.append(car_to_am[tok])
        i += len(tok)
    return "".join(out)


def decode_latin_word_to_candidates(
    word: str,
    car_to_am: Dict[str, str],
    latin_mode: str = "auto",
    habit_strength: float = 1.0,
) -> List[Candidate]:
    """
    Decode a single Latin "word" into Candidate CAR strings.

    Core Latin-Std rules:
    - Uppercase carriers AA/EE/A/U/I/O/E are standalone carriers (a1..a7), never vowel cues.
    - "Ei" after a consonant is reserved for order-5 (e.g., hEi -> ሄ).
    - Explicit base selectors work in AUTO and STRICT:
        K,N,Z,X,P,T,C (case-sensitive)
      plus lowercase 'c' is a convenience alias for 'ch' (ቸ).
    """
    w = word.strip()
    if not w:
        return []

    # --------------------
    # STRICT MODE
    # --------------------
    if latin_mode == "strict":
        car = ""
        i = 0
        while i < len(w):
            ch = w[i]
            forced_var = None
            # single-letter explicit base selectors
            if ch in STRICT_BASE_MAP:
                # base = STRICT_BASE_MAP[ch]
                v = STRICT_BASE_MAP[ch]
                forced_var = None
                if isinstance(v, tuple):
                    base, forced_var = v
                else:
                    base = v
                i += 1
            # lowercase convenience: c -> ch
            elif ch == "c":
                base = "ch"
                i += 1
            else:
                base = ch.lower()
                i += 1

            # ejective mark (still allowed explicitly)
            if i < len(w) and w[i] == "'":
                base += "'"
                i += 1

            # var = ""
            # if i < len(w) and w[i] in "12":
            #     var = w[i]
            #     i += 1

            # if i >= len(w) or not w[i].isdigit():
            #     return []
            # order = w[i]
            # i += 1
            var = ""
            if i < len(w) and w[i] in "12":
                var = w[i]
                i += 1

            # apply forced variant if selector demands it
            if forced_var is not None:
                if var and var != forced_var:
                    return []  # conflicting variant; invalid strict token
                var = forced_var

            if i >= len(w) or not w[i].isdigit():
                return []
            order = w[i]
            i += 1

            tok = f"{base}{var}{order}"
            if tok not in car_to_am:
                return []
            car += tok

        return [Candidate(car=car, score=5.0, reasons=["strict_mode"])]

    # --------------------
    # AUTO MODE
    # --------------------
    wraw = w
    wlow = w.lower()

    # clamp habit strength
    habit_strength = max(0.0, min(1.0, habit_strength))

    # 0) Lexicon fast-path
    if wlow in LAT_LEXICON:
        car = LAT_LEXICON[wlow]
        if try_decode_car_concatenation(car, car_to_am) is not None:
            return [Candidate(car=car, score=3.0, reasons=["lexicon"])]

    # 1) Try direct CAR concatenation
    maybe = try_decode_car_concatenation(w, car_to_am)
    if maybe is not None:
        return [Candidate(car=w, score=0.99, reasons=["parsed_as_car"])]

    def upper_carrier_start_at(raw: str, j: int) -> bool:
        if j >= len(raw):
            return False
        # Ei is order-5 cue, not a carrier
        if j + 1 < len(raw) and raw[j:j+2] == "Ei":
            return False
        if j + 1 < len(raw) and raw[j:j+2] in ("AA", "EE"):
            return True
        if raw[j] in ("A", "U", "I", "O", "E"):
            return True
        return False

    def digraph_habit_bonus(raw: str, pos0: int) -> float:
        base = HABIT_DIGRAPH_BONUS
        prev_ch = raw[pos0 - 1] if pos0 - 1 >= 0 else ""
        next_ch = raw[pos0 + 2] if pos0 + 2 < len(raw) else ""
        if prev_ch in ("-", "_", "'") or next_ch in ("-", "_", "'"):
            return 0.0
        if prev_ch and next_ch and prev_ch.isalpha() and next_ch.isalpha():
            return base
        return base

    # Beam entries: (pos, car_str, score, reasons)
    beam: List[Tuple[int, str, float, List[str]]] = [(0, "", 0.0, [])]
    max_beam = 20

    def add(beam_next, pos, car_add, score_add, reasons_add):
        beam_next.append((pos, car_add, score_add, reasons_add))

    def emit_base_step(
        new_beam: List[Tuple[int, str, float, List[str]]],
        pos_after_base: int,
        base: str,
        var: str,
        base_score: float,
        base_reasons2: List[str],
        car_str: str,
        wraw: str,
        wlow: str,
    ) -> bool:
        """
        Emit transitions after we've identified a base (+ optional variant),
        applying vowel cues or no-vowel (order6). Returns whether progressed.
        """
        progressed_local = False
        b_end2 = pos_after_base

        # carriers never act as vowel cues
        if upper_carrier_start_at(wraw, b_end2):
            tok = f"{base}{var}6"
            if tok in car_to_am:
                add(new_beam, b_end2, car_str + tok, base_score + 0.55,
                    base_reasons2 + ["carrier_boundary->order6"])
                return True
            return False

        matched_vowel = False

        # Prefer explicit Ei for order5
        if b_end2 + 1 < len(wraw) and wraw[b_end2:b_end2+2] == "Ei":
            tok = f"{base}{var}5"
            if tok in car_to_am:
                add(new_beam, b_end2 + 2, car_str + tok, base_score + 0.75,
                    base_reasons2 + ["vowel2=Ei(explicit)"])
                progressed_local = True
                matched_vowel = True
        # Prefer explicit Wa for order8
        # if (not matched_vowel) and b_end2 + 1 < len(wraw) and wraw[b_end2:b_end2+2] == "Wa":
        #     tok = f"{base}{var}8"
        #     if tok in car_to_am:
        #         add(
        #             new_beam,
        #             b_end2 + 2,
        #             car_str + tok,
        #             base_score + 0.75,
        #             base_reasons2 + ["vowel2=Wa(explicit)"],
        #         )
        #         progressed_local = True
        #         matched_vowel = True

        # Prefer explicit Wa for order8
        if (not matched_vowel) and b_end2 + 1 < len(wraw) and wraw[b_end2:b_end2+2] == "Wa":
            # first: normal path (base8)
            tok = f"{base}{var}8"
            if tok in car_to_am:
                add(
                    new_beam,
                    b_end2 + 2,
                    car_str + tok,
                    base_score + 0.75,
                    base_reasons2 + ["vowel2=Wa(explicit)"],
                )
                progressed_local = True
                matched_vowel = True
            else:
                # exceptional convenience: hWa means khWa (because only kh has order8 /wa/)
                if base == "h" and var == "":
                    tok2 = "kh8"
                    if tok2 in car_to_am:
                        add(
                            new_beam,
                            b_end2 + 2,
                            car_str + tok2,
                            base_score + 0.72,  # slightly less than explicit khWa, but still strong
                            base_reasons2 + ["vowel2=Wa(explicit)", "exception:hWa->kh8"],
                        )
                        progressed_local = True
                        matched_vowel = True


        # 2-letter vowel cue (lowercase ei)
        if (not matched_vowel) and b_end2 + 1 < len(wlow):
            v2 = wlow[b_end2:b_end2 + 2]
            # IMPORTANT (bijective Latin-Std): 2-letter lowercase vowel cues must match in the *raw* text too.
            # This prevents consuming uppercase carriers like 'I' in sequences such as 'eI' (e.g., beItyoPya).
            if wraw[b_end2:b_end2 + 2] != v2:
                v2 = ""
            if v2 in VOWEL2_TO_ORDER:
                order = VOWEL2_TO_ORDER[v2]
                tok = f"{base}{var}{order}"
                if tok in car_to_am:
                    add(new_beam, b_end2 + 2, car_str + tok, base_score + 0.6,
                        base_reasons2 + [f"vowel2={v2}"])
                    progressed_local = True
                    matched_vowel = True

        # 1-letter vowel cue (lowercase only)
        if (not matched_vowel) and b_end2 < len(wlow):
            v1 = wlow[b_end2]
            if v1 in VOWEL_TO_ORDER:
                order = VOWEL_TO_ORDER[v1]
                tok = f"{base}{var}{order}"
                if tok in car_to_am:
                    add(new_beam, b_end2 + 1, car_str + tok, base_score + 0.5,
                        base_reasons2 + [f"vowel={v1}"])
                    progressed_local = True
                    matched_vowel = True

                    # habit alternative: i sometimes used as "no vowel" (order6)
                    if v1 == "i" and (b_end2 + 1) < len(wlow):
                        nxt = wlow[b_end2 + 1]
                        if nxt.isalpha() or nxt == "'":
                            tok2 = f"{base}{var}6"
                            if tok2 in car_to_am:
                                add(new_beam, b_end2 + 1, car_str + tok2,
                                    base_score + 0.05,
                                    base_reasons2 + ["habit:i->order6"])
                                progressed_local = True

        # no vowel => order6 only
        if not matched_vowel:
            tok = f"{base}{var}6"
            if tok in car_to_am:
                add(new_beam, b_end2, car_str + tok, base_score + 0.1,
                    base_reasons2 + ["no_vowel->order6"])
                progressed_local = True

        return progressed_local

    while True:
        progressed = False
        new_beam: List[Tuple[int, str, float, List[str]]] = []

        for pos, car_str, score, reasons in beam:
            if pos >= len(wlow):
                new_beam.append((pos, car_str, score, reasons))
                continue

            ch = wlow[pos]

            # separators inside token
            if ch in "-_":
                new_beam.append((pos + 1, car_str, score - 0.2, reasons + ["skipped_sep"]))
                progressed = True
                continue

            # (0) Latin-Std carriers at cursor (case-sensitive)
            if pos < len(wraw):
                if pos + 1 < len(wraw) and wraw[pos:pos+2] in ("AA", "EE"):
                    carr = wraw[pos:pos+2]
                    tok = LATIN_STD_CARRIERS[carr]
                    if tok in car_to_am:
                        add(new_beam, pos + 2, car_str + tok, score + 0.8,
                            reasons + [f"carrier={carr}->{tok}"])
                        progressed = True
                        continue

                if wraw[pos] in ("A", "U", "I", "O", "E"):
                    carr = wraw[pos]
                    tok = LATIN_STD_CARRIERS[carr]
                    if tok in car_to_am:
                        add(new_beam, pos + 1, car_str + tok, score + 0.7,
                            reasons + [f"carrier={carr}->{tok}"])
                        progressed = True
                        continue

            # (0b) Latin-Std explicit base selectors (case-sensitive): K,N,Z,X,P,T,C
            if pos < len(wraw) and wraw[pos] in STRICT_BASE_MAP:
                # base = STRICT_BASE_MAP[wraw[pos]]
                v = STRICT_BASE_MAP[wraw[pos]]
                forced_var = None
                if isinstance(v, tuple):
                    base, forced_var = v
                else:
                    base = v

                b_end = pos + 1
                base_score = score + 0.9
                base_reasons = reasons + [f"strict_base={wraw[pos]}->{base}"]

                var = ""
                if b_end < len(wlow) and wlow[b_end] in "12":
                    var = wlow[b_end]
                    b_end2 = b_end + 1
                    base_score += 0.3
                    base_reasons2 = base_reasons + [f"variant={var}"]
                else:
                    b_end2 = b_end
                    base_reasons2 = base_reasons
                # apply forced variant if selector demands it
                if forced_var is not None:
                    if var and var != forced_var:
                        # conflict: explicit variant digit contradicts selector
                        continue
                    var = forced_var

                if emit_base_step(new_beam, b_end2, base, var, base_score, base_reasons2, car_str, wraw, wlow):
                    progressed = True
                continue

            # (0c) Latin-Std lowercase convenience alias: c -> ch (ቸ)
            if pos < len(wraw) and wraw[pos] == "c":
                base = "ch"
                b_end2 = pos + 1
                base_score = score + 0.88
                base_reasons2 = reasons + ["alias_base=c->ch"]
                if emit_base_step(new_beam, b_end2, base, "", base_score, base_reasons2, car_str, wraw, wlow):
                    progressed = True
                continue

            matched_any = False

            # (A) Case-marked digraphs: Sh/Kh/Ny/Zh/Ch
            if pos + 1 < len(wraw):
                dig2 = wraw[pos:pos+2]
                base_cd = CASE_DIGRAPHS.get(dig2)
                if base_cd is not None:
                    matched_any = True
                    base = base_cd
                    b_end = pos + 2
                    base_score = score + 0.9
                    base_reasons = reasons + [f"case_digraph={dig2}->{base}"]

                    var = ""
                    if b_end < len(wlow) and wlow[b_end] in "12":
                        var = wlow[b_end]
                        b_end2 = b_end + 1
                        base_score += 0.3
                        base_reasons2 = base_reasons + [f"variant={var}"]
                    else:
                        b_end2 = b_end
                        base_reasons2 = base_reasons

                    if emit_base_step(new_beam, b_end2, base, var, base_score, base_reasons2, car_str, wraw, wlow):
                        progressed = True

            # (A2) Habit support (AUTO): lowercase digraphs as single base, as alternatives
            if pos + 1 < len(wlow):
                dig2_low = wlow[pos:pos+2]
                if dig2_low in AUTO_DISABLED_BASES:
                    matched_any = True
                    base = dig2_low
                    b_end = pos + 2

                    base_score = score + habit_strength * digraph_habit_bonus(wraw, pos)
                    base_reasons = reasons + [f"habit_digraph={dig2_low}->{base}"]

                    var = ""
                    if b_end < len(wlow) and wlow[b_end] in "12":
                        var = wlow[b_end]
                        b_end2 = b_end + 1
                        base_score += 0.1
                        base_reasons2 = base_reasons + [f"variant={var}"]
                    else:
                        b_end2 = b_end
                        base_reasons2 = base_reasons

                    if emit_base_step(new_beam, b_end2, base, var, base_score, base_reasons2, car_str, wraw, wlow):
                        progressed = True

            # (B) Standard base matching. Lowercase digraph bases are disabled.
            for base in BASES:
                if base in AUTO_DISABLED_BASES:
                    continue
                if wlow.startswith(base, pos):
                    matched_any = True
                    b_end = pos + len(base)
                    base_score = score + (0.8 if base.endswith("'") else 0.2)
                    base_reasons = reasons + (["ejective_marked"] if base.endswith("'") else [])

                    var = ""
                    if b_end < len(wlow) and wlow[b_end] in "12":
                        var = wlow[b_end]
                        b_end2 = b_end + 1
                        base_score += 0.3
                        base_reasons2 = base_reasons + [f"variant={var}"]
                    else:
                        b_end2 = b_end
                        base_reasons2 = base_reasons

                    if emit_base_step(new_beam, b_end2, base, var, base_score, base_reasons2, car_str, wraw, wlow):
                        progressed = True

            if not matched_any:
                new_beam.append((pos + 1, car_str, score - 1.5, reasons + [f"skipped:{wlow[pos]}"]))
                progressed = True

        new_beam.sort(key=lambda x: x[2], reverse=True)
        beam = new_beam[:max_beam]

        if all(pos >= len(wlow) for pos, *_ in beam):
            break
        if not progressed:
            break

    candidates: List[Candidate] = []
    for pos, car_str, score, reasons in beam:
        if pos == len(wlow) and car_str:
            candidates.append(Candidate(car=car_str, score=score, reasons=reasons))

    best_by_car: Dict[str, Candidate] = {}
    for c in candidates:
        prev = best_by_car.get(c.car)
        if prev is None or c.score > prev.score:
            best_by_car[c.car] = c

    out = list(best_by_car.values())
    out.sort(key=lambda c: c.score, reverse=True)
    return out[:5]


def score_to_confidence(scores: List[float]) -> Tuple[float, List[float]]:
    if not scores:
        return 0.0, []
    confs = [1 / (1 + math.exp(-s)) for s in scores]
    best = max(confs)
    normed = [c / best if best > 0 else 0.0 for c in confs]
    return normed[0], normed


# ---- Main normalize function ----
def normalize(text: str, options: Optional[Dict] = None) -> Dict:
    car_to_am, am_to_car = load_car_maps()

    options = options or {}
    latin_mode = options.get("latin_mode", "auto")

    text = normalize_ethiopic_text(text)
    spans = segment_scripts(text)

    out_text_parts: List[str] = []
    span_meta = []
    alternatives_accum: List[Dict] = []
    overall_conf = 1.0
    warnings: List[str] = []

    return_alts = bool(options.get("return_alternatives", True))
    max_alts = int(options.get("max_alternatives", 3))
    if max_alts < 0:
        max_alts = 0

    hs = float(options.get("habit_strength", 0.85))
    hs = max(0.0, min(1.0, hs))

    for sp in spans:
        if sp.kind == "ETH":
            out_text_parts.append(sp.text)
            span_meta.append({"kind": "ETH", "text": sp.text})

        elif sp.kind == "LAT":
            # chunks = re.findall(r"[A-Za-z'0-9]+|[^A-Za-z'0-9]+", sp.text)
            chunks = re.findall(r"[A-Za-z']+|[^A-Za-z']+", sp.text)
            for chunk in chunks:
                # if re.fullmatch(r"[A-Za-z'0-9]+", chunk):
                if re.fullmatch(r"[A-Za-z']+", chunk):
                    cand = decode_latin_word_to_candidates(
                        chunk,
                        car_to_am,
                        latin_mode=latin_mode,
                        habit_strength=hs,
                    )

                    if not cand:
                        out_text_parts.append(chunk)
                        span_meta.append({"kind": "LAT", "text": chunk, "decoded": False})
                        warnings.append("latin_decode_failed")
                        overall_conf *= 0.5
                        continue

                    scores = [c.score for c in cand]
                    best_conf, confs = score_to_confidence(scores)

                    best = cand[0]
                    decoded = try_decode_car_concatenation(best.car, car_to_am)
                    if decoded is None:
                        out_text_parts.append(chunk)
                        span_meta.append({"kind": "LAT", "text": chunk, "decoded": False})
                        warnings.append("latin_decode_failed")
                        overall_conf *= 0.5
                        continue

                    out_text_parts.append(decoded)
                    span_meta.append({
                        "kind": "LAT",
                        "text": chunk,
                        "decoded": True,
                        "best_car": best.car,
                        "confidence": best_conf,
                        "reasons": best.reasons,
                        "num_alternatives": max(0, len(cand) - 1),
                    })

                    if return_alts and len(cand) > 1 and max_alts > 0:
                        for idx, c in enumerate(cand[1:]):
                            if len(alternatives_accum) >= max_alts:
                                break
                            alt_dec = try_decode_car_concatenation(c.car, car_to_am)
                            if alt_dec is None:
                                continue
                            alternatives_accum.append({
                                "text_am": alt_dec,
                                "car": c.car,
                                "confidence": confs[idx + 1] if idx + 1 < len(confs) else 0.0,
                                "reason": ";".join(c.reasons),
                                "source": chunk,
                            })
                        overall_conf *= min(1.0, best_conf)

                else:
                    out_text_parts.append(chunk)
                    span_meta.append({"kind": "SEP", "text": chunk})

        else:
            out_text_parts.append(sp.text)
            span_meta.append({"kind": sp.kind, "text": sp.text})

    # out_text = "".join(out_text_parts)
    # out_text = normalize_ethiopic_text(out_text)

    # 
    out_text = "".join(out_text_parts)
    # NEW: map ASCII punctuation (from Latin spans) into Ethiopic punctuation
    out_text = ascii_punct_to_ethiopic(out_text)
    # existing: ፡ -> space + collapse whitespace
    out_text = normalize_ethiopic_text(out_text)
    # 


    car_out_parts: List[str] = []
    for ch in out_text:
        if ch in am_to_car:
            car_out_parts.append(am_to_car[ch])
        else:
            car_out_parts.append(ch)
    car_out = "".join(car_out_parts)

    overall_conf = max(0.0, min(1.0, overall_conf))

    return {
        "text_am": out_text,
        "car": car_out,
        "confidence": overall_conf,
        "alternatives": alternatives_accum,
        "meta": {
            "spans": span_meta,
            "warnings": sorted(set(warnings)),
        },
    }


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--json":
        inp = sys.argv[2]
    else:
        inp = sys.stdin.read()
    res = normalize(inp)
    sys.stdout.write(json.dumps(res, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()



