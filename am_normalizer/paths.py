from __future__ import annotations
from importlib.resources import files
from pathlib import Path

def data_path(*parts: str) -> Path:
    # importlib.resources returns Traversable
    return Path(files("am_normalizer").joinpath("data", *parts))