#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"

def read_tsv(path: Path):
    rows = []
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

def load_car_to_am():
    car_to_am = {}
    for r in read_tsv(TABLES / "orders.tsv"):
        token = f'{r["base"]}{r.get("variant","")}{r["order"]}'
        car_to_am[token] = r["char"]
    for r in read_tsv(TABLES / "order8.tsv"):
        token = f'{r["base"]}{r.get("variant","")}{r["order"]}'
        car_to_am[token] = r["char"]
    return car_to_am

def decode_stream(s: str, car_to_am: dict) -> str:
    i = 0
    out = []
    while i < len(s):
        c = s[i]
        if not (c.isalpha() or c == "'"):
            out.append(c)
            i += 1
            continue

        # Read base up to first digit
        j = i
        while j < len(s) and not s[j].isdigit():
            j += 1
        if j >= len(s):
            # trailing base without order digit
            raise ValueError(f"Invalid token at end near: {s[i:]}")
        # Try (base + variant + order) first (two digits)
        tok = None
        if j + 1 < len(s) and s[j].isdigit() and s[j+1].isdigit():
            cand = s[i:j] + s[j] + s[j+1]
            if cand in car_to_am:
                tok = cand
        if tok is None:
            cand = s[i:j] + s[j]
            if cand in car_to_am:
                tok = cand
        if tok is None:
            raise ValueError(f"Unknown token near: {s[i:i+10]}")
        out.append(car_to_am[tok])
        i += len(tok)
    return "".join(out)

def main():
    car_to_am = load_car_to_am()
    s = sys.stdin.read()
    sys.stdout.write(decode_stream(s, car_to_am))

if __name__ == "__main__":
    main()

