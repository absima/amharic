#!/usr/bin/env python3
"""
AN-v0 Normalizer (reference implementation)

- Uses CAR tables in tables/orders.tsv and tables/order8.tsv
- Stage A: segment scripts
- Stage B: Ethiopic normalization (whitespace + ፡ -> space)
- Stage C: Latin decoding (outer-layer Latin-Std -> CAR, ambiguity surfaced)
- Stage D/E: merge + final CAR encoding
"""

from __future__ import annotations

import json
import math
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .paths import data_path

TABLES = data_path("tables")


# Ethiopic basic block range (good enough for Amharic v0 work)
def is_ethiopic_char(ch: str) -> bool:
    o = ord(ch)
    return 0x1200 <= o <= 0x137F


def is_latin_char(ch: str) -> bool:
    # Include '_' because we use underscore carriers like _a, _ei, _ (a6).
    # Include apostrophe as pass-through for future prosody/stress layers.
    return ("a" <= ch <= "z") or ("A" <= ch <= "Z") or ch in {"'", "_"}


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


@lru_cache(maxsize=1)
def load_car_maps_cached() -> Tuple[Dict[str, str], Dict[str, str]]:
    return load_car_maps()


# ---- Stage B: Ethiopic normalization (v0) ----
# Preserve spaces/newlines; only normalize ፡ -> space
def normalize_ethiopic_text(s: str) -> str:
    return (s or "").replace("፡", " ")


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
        if idx < 1 or not s[idx - 1].isalpha():
            return False
        j = idx - 2
        while j >= 0 and s[j] in " \t":
            j -= 1
        return (j >= 1 and s[j] == "." and s[j - 1].isalpha())

    while i < n:
        ch = s[i]

        if ch in ASCII_TO_ETH_PUNCT:
            out.append(ASCII_TO_ETH_PUNCT[ch])
            i += 1
            continue

        if ch == ":":
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

            # default: convert to ። when it looks like sentence end
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

    cur_kind = base_kind(s[0])
    buf = [s[0]]

    for i in range(1, len(s)):
        k = base_kind(s[i])
        if k == cur_kind:
            buf.append(s[i])
        else:
            spans.append(Span(cur_kind, "".join(buf)))
            cur_kind = k
            buf = [s[i]]

    spans.append(Span(cur_kind, "".join(buf)))
    return spans


# ---- Stage C: Latin decoding (outer Latin-Std) ----

# Canonical Latin-Std base tokens (outer layer).
# IMPORTANT: longest-match matters; keep longer tokens first.
BASES = [
    # very long first
    "cxx", "chx", "shx", "hxx",
    # x-marked bases
    "kx", "nx", "zx", "cx", "px", "tx", "hx", "sx", "ax",
    # regular digraphs (if you still accept them as-is)
    "ch", "sh", "kh", "ny", "zh",
    # singles
    "h", "l", "m", "r", "s", "q", "b", "t", "n", "k", "w", "z", "y", "d", "j", "g", "f", "p", "v",
]

# Attached vowel cues after consonant families
VOWEL_TO_ORDER = {"e": "1", "u": "2", "i": "3", "a": "4", "o": "7"}
VOWEL2_TO_ORDER = {"ei": "5"}

# Independent vowel carriers (a-family), underscore-prefixed:
# _a,_u,_i,_aa,_ei,_,_o -> አ ኡ ኢ ኣ ኤ እ ኦ
UNDERSCORE_CARRIERS = {
    "_a":  "a1",
    "_u":  "a2",
    "_i":  "a3",
    "_aa": "a4",
    "_ei": "a5",
    "_":   "a6",
    "_o":  "a7",
}

# Optional lexicon fast-path
LAT_LEXICON = {
    "yet": "y1t6",   # የት
    "bota": "b7t4",  # ቦታ
    "mn": "m6n6",    # ምን
    "min": "m6n6",   # ምን
}

# Latin-Std base token -> (car_base, forced_variant)
# forced_variant is "1"/"2" or "" when not needed.
LATIN_BASE_TO_CAR = {
    # “not in Latin” / ejective / special
    "kx":  ("kh",  ""),
    "nx":  ("ny",  ""),
    "zx":  ("zh",  ""),
    "cx":  ("ts'", ""),
    "px":  ("p'",  ""),
    "tx":  ("t'",  ""),
    "chx": ("ch'", ""),
    "shx": ("sh",  ""),

    # variant families
    "hx":  ("h",   "1"),  # ሐ
    "hxx": ("h",   "2"),  # ኀ
    "sx":  ("s",   "1"),  # ሠ
    "ax":  ("a",   "1"),  # ዐ (a-family variant treated as consonant family)
    "cxx": ("ts'", "1"),  # ፀ (variant of ጸ in your tables)

    # plain ones map to themselves implicitly: "ch","h","l","m",...
}

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
    habit_strength: float = 0.0,
) -> List[Candidate]:
    """
    Decode a single Latin "word" into Candidate CAR strings.

    Outer Latin-Std (case-free) rules:
    - Underscore carriers:
        _a,_u,_i,_aa,_ei,_,_o -> a1..a7
    - Attached vowels:
        e,u,i,a,ei,(empty),o -> orders 1..7
    - Override vowels as አ-family after a consonant:
        C _vowel  => C6 + a(order)
        Example: l_u => l6 a2 => ልኡ
    - Order-8 labialized suffix:
        C oa => C8
        Example: loa => l8 => ሏ
    - Apostrophe (') is pass-through (reserved for future prosody); it is NOT an ejective marker here.
    """
    w = (word or "").strip()
    if not w:
        return []

    # "strict" is deprecated in the case-free standard; treat as auto
    if latin_mode == "strict":
        latin_mode = "auto"

    wraw = w
    wlow = w.lower()

    # 0) Lexicon fast-path (lowercased lookup)
    if wlow in LAT_LEXICON:
        car = LAT_LEXICON[wlow]
        if try_decode_car_concatenation(car, car_to_am) is not None:
            return [Candidate(car=car, score=3.0, reasons=["lexicon"])]

    # 1) Try direct CAR concatenation
    maybe = try_decode_car_concatenation(w, car_to_am)
    if maybe is not None:
        return [Candidate(car=w, score=0.99, reasons=["parsed_as_car"])]

    # Beam entries: (pos, car_str, score, reasons)
    beam: List[Tuple[int, str, float, List[str]]] = [(0, "", 0.0, [])]
    max_beam = 20

    def add(beam_next, pos, car_add, score_add, reasons_add):
        beam_next.append((pos, car_add, score_add, reasons_add))

    def match_underscore_carrier(raw: str, pos: int) -> Optional[Tuple[str, str, int]]:
        """
        If raw[pos:] starts with an underscore-carrier, return (key, tok, length).
        Longest-match first.
        """
        if pos >= len(raw) or raw[pos] != "_":
            return None
        for key in ("_aa", "_ei", "_a", "_u", "_i", "_o", "_"):
            if raw.startswith(key, pos):
                return key, UNDERSCORE_CARRIERS[key], len(key)
        return None
    def match_leading_vowel_as_a_family(raw: str, pos: int) -> Optional[Tuple[str, str, int]]:
        """
        Input convenience: at word-start only, allow leading vowels to mean a-family carriers,
        as if prefixed with underscore.

        a,u,i,aa,ei,o -> a1,a2,a3,a4,a5,a7
        e             -> a6  (because _ alone is your እ carrier)
        """
        if pos != 0:
            return None

        # longest-match first
        if raw.startswith("aa", pos):
            return "aa", "a4", 2
        if raw.startswith("ei", pos):
            return "ei", "a5", 2

        ch = raw[pos:pos+1].lower()
        if ch == "a":
            return "a", "a1", 1
        if ch == "u":
            return "u", "a2", 1
        if ch == "i":
            return "i", "a3", 1
        if ch == "o":
            return "o", "a7", 1
        if ch == "e":
            return "e", "a6", 1

        return None    
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
        After we've identified a base (+ optional variant), emit possible transitions:
        - order8 via "oa"
        - underscore override: C _carrier => C6 + a#
        - attached vowels ei/e/u/i/a/o
        - no vowel => order6
        """
        b_end2 = pos_after_base
        progressed_local = False

        # (1) Special order-8 suffix: "oa"
        if b_end2 + 1 < len(wlow) and wlow[b_end2:b_end2 + 2] == "oa":
            tok = f"{base}{var}8"
            if tok in car_to_am:
                add(new_beam, b_end2 + 2, car_str + tok, base_score + 0.85,
                    base_reasons2 + ["vowel2=oa(order8)"])
                return True
            # if base doesn't support order8, fall through

        # (2) Underscore override after consonant: C _carrier => C6 + a(order)
        m = match_underscore_carrier(wraw, b_end2)
        if m is not None:
            key, a_tok, klen = m
            tok_c6 = f"{base}{var}6"
            if tok_c6 in car_to_am and a_tok in car_to_am:
                add(new_beam, b_end2 + klen, car_str + tok_c6 + a_tok, base_score + 0.9,
                    base_reasons2 + [f"underscore_override={key}->{tok_c6}+{a_tok}"])
                progressed_local = True
                # do not return; allow other paths too (beam search)

        matched_vowel = False

        # (3) 2-letter attached vowel cue "ei" (lowercase only)
        if b_end2 + 1 < len(wlow):
            v2 = wlow[b_end2:b_end2 + 2]
            if v2 in VOWEL2_TO_ORDER:
                order = VOWEL2_TO_ORDER[v2]
                tok = f"{base}{var}{order}"
                if tok in car_to_am:
                    add(new_beam, b_end2 + 2, car_str + tok, base_score + 0.6,
                        base_reasons2 + [f"vowel2={v2}"])
                    progressed_local = True
                    matched_vowel = True

        # (4) 1-letter attached vowel cue
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

        # (5) no attached vowel => order6
        tok6 = f"{base}{var}6"
        if tok6 in car_to_am:
            add(new_beam, b_end2, car_str + tok6, base_score + 0.1,
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

            # hyphen is treated as a soft separator; skip with small penalty
            if ch == "-":
                new_beam.append((pos + 1, car_str, score - 0.2, reasons + ["skipped_sep:-"]))
                progressed = True
                continue

            # apostrophe is reserved for future prosody/stress; keep as passthrough by skipping
            if ch == "'":
                new_beam.append((pos + 1, car_str, score - 0.15, reasons + ["skipped_apostrophe"]))
                progressed = True
                continue

            # (0) underscore carriers at cursor: _a/_u/_i/_aa/_ei/_/_o
            m0 = match_underscore_carrier(wraw, pos)
            if m0 is not None:
                key, tok, klen = m0
                if tok in car_to_am:
                    add(new_beam, pos + klen, car_str + tok, score + 0.9,
                        reasons + [f"underscore_carrier={key}->{tok}"])
                    progressed = True
                    continue
            # (0a) leading vowels at word-start behave like a-family carriers
            mv = match_leading_vowel_as_a_family(wraw, pos)
            if mv is not None:
                key, tok, klen = mv
                if tok in car_to_am:
                    add(new_beam, pos + klen, car_str + tok, score + 0.85,
                        reasons + [f"leading_vowel={key}->{tok}"])
                    progressed = True
                    continue
            matched_any = False

            # (1) Standard base matching (longest-match because BASES ordered)
            # for base in BASES:
            #     if wlow.startswith(base, pos):
            #         matched_any = True
            #         b_end = pos + len(base)

            #         # outer Latin-Std: no explicit variant digits here; variants are encoded in the base token itself (hx/hxx/cxx/etc.)
            #         var = ""
            #         base_score = score + 0.35
            #         base_reasons = reasons + [f"base={base}"]

            #         if emit_base_step(new_beam, b_end, base, var, base_score, base_reasons, car_str, wraw, wlow):
            #             progressed = True
            for base_tok in BASES:
                if wlow.startswith(base_tok, pos):
                    matched_any = True
                    b_end = pos + len(base_tok)

                    # Map Latin base token -> CAR base (+ forced variant if needed)
                    forced_var = ""
                    if base_tok in LATIN_BASE_TO_CAR:
                        car_base, forced_var = LATIN_BASE_TO_CAR[base_tok]
                    else:
                        car_base = base_tok  # plain bases

                    var = forced_var  # outer layer encodes variants in the token itself
                    base_score = score + 0.35
                    base_reasons = reasons + [f"base={base_tok}->{car_base}{var}"]

                    if emit_base_step(new_beam, b_end, car_base, var, base_score, base_reasons, car_str, wraw, wlow):
                        progressed = True
            if not matched_any:
                # Unknown character inside LAT chunk: skip (penalize) and continue.
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

    hs = float(options.get("habit_strength", 0.0))
    hs = max(0.0, min(1.0, hs))

    for sp in spans:
        if sp.kind == "ETH":
            out_text_parts.append(sp.text)
            span_meta.append({"kind": "ETH", "text": sp.text})

        elif sp.kind == "LAT":
            # Keep underscore and apostrophe in Latin “word” chunks:
            chunks = re.findall(r"[A-Za-z'_]+|[^A-Za-z'_]+", sp.text)
            for chunk in chunks:
                if re.fullmatch(r"[A-Za-z'_]+", chunk):
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

    out_text = "".join(out_text_parts)
    out_text = ascii_punct_to_ethiopic(out_text)
    out_text = normalize_ethiopic_text(out_text)

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
