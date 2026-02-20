#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "tables"
TESTS = ROOT / "tests"

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

def load_maps():
    orders = read_tsv(TABLES / "orders.tsv")
    order8 = read_tsv(TABLES / "order8.tsv")

    car_to_am = {}
    am_to_car = {}

    def add_row(row):
        base = row["base"]
        var = row.get("variant", "")
        order = row["order"]
        ch = row["char"]
        token = f"{base}{var}{order}"
        car_to_am[token] = ch
        am_to_car[ch] = token

    for r in orders:
        add_row(r)
    for r in order8:
        add_row(r)

    return car_to_am, am_to_car

def check_roundtrip(car_to_am, am_to_car):
    # Ethiopic -> CAR -> Ethiopic
    for ch, token in am_to_car.items():
        back = car_to_am.get(token)
        if back != ch:
            raise AssertionError(f"Roundtrip failed: {ch} -> {token} -> {back}")

    # CAR -> Ethiopic -> CAR
    for token, ch in car_to_am.items():
        back = am_to_car.get(ch)
        if back != token:
            raise AssertionError(f"Roundtrip failed: {token} -> {ch} -> {back}")

def check_tests(car_to_am, am_to_car):
    def load_json(name):
        p = TESTS / name
        if not p.exists() or p.stat().st_size == 0:
            return []
        return json.loads(p.read_text(encoding="utf-8"))

    for name in ["characters.json", "minimal_pairs.json", "words.json"]:
        data = load_json(name)
        for item in data:
            am = item["am"]
            car = item["car"]
            # encode
            enc = "".join(am_to_car.get(c, c) for c in am)
            if enc != car:
                raise AssertionError(f"{name}: encode mismatch: {am} expected {car} got {enc}")
            # decode
            # (simple decode assumes tokens are concatenated, which they are in tests)
            # We'll decode by greedy matching from maps (safe here).
            i = 0
            out = []
            while i < len(car):
                # find next token end (must end with digit 1-8)
                if car[i].isspace():
                    out.append(car[i]); i += 1; continue
                # read base+optional apostrophe and optional variant digit then order digit
                j = i
                while j < len(car) and not car[j].isdigit():
                    j += 1
                # now at first digit of (variant or order)
                # order is always last digit of token; variant is optional digit before it
                # so token ends at j+1 if only order, or j+2 if variant+order.
                # Decide by looking ahead: if two digits and second is 1-8, treat first as variant.
                tok = None
                if j + 1 < len(car) and car[j].isdigit() and car[j+1].isdigit():
                    cand = car[i:j] + car[j] + car[j+1]
                    if cand in car_to_am:
                        tok = cand
                if tok is None:
                    cand = car[i:j] + car[j]
                    if cand in car_to_am:
                        tok = cand
                if tok is None:
                    raise AssertionError(f"{name}: cannot decode at pos {i}: {car[i:i+10]}")
                out.append(car_to_am[tok])
                i += len(tok)
            dec = "".join(out)
            if dec != am:
                raise AssertionError(f"{name}: decode mismatch: {car} expected {am} got {dec}")

def main():
    car_to_am, am_to_car = load_maps()
    check_roundtrip(car_to_am, am_to_car)
    check_tests(car_to_am, am_to_car)
    print("OK: tables + tests validated.")

if __name__ == "__main__":
    main()

