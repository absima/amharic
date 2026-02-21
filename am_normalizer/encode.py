#!/usr/bin/env python3
import sys
from .paths import data_path

TABLES = data_path("tables")

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

def load_am_to_car():
    am_to_car = {}
    for r in read_tsv(TABLES / "orders.tsv"):
        token = f'{r["base"]}{r.get("variant","")}{r["order"]}'
        am_to_car[r["char"]] = token
    for r in read_tsv(TABLES / "order8.tsv"):
        token = f'{r["base"]}{r.get("variant","")}{r["order"]}'
        am_to_car[r["char"]] = token
    return am_to_car

def main():
    am_to_car = load_am_to_car()
    text = sys.stdin.read()
    out = []
    for c in text:
        out.append(am_to_car.get(c, c))
    sys.stdout.write("".join(out))

if __name__ == "__main__":
    main()

