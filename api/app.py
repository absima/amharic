import json
import sys
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from am_normalizer.normalize import normalize  # type: ignore  # noqa: E402
from am_normalizer.ui_resolver import resolve_ui_key  # noqa: E402
from am_normalizer.latin_std import car_to_latin_std, ethiopic_punct_to_ascii  # type: ignore  # noqa: E402



ROOT = Path(__file__).resolve().parents[1]


# --- load env (ensure we load the repo-root .env even if cwd differs) ---
load_dotenv()

def _get_cors_origins() -> list[str]:
    """
    it reads CORS_ORIGINS from env.
    and accepts either:
      - comma-separated:  http://a,http://b
      - or JSON array:    ["http://a","http://b"]
    """
    raw = (os.getenv("CORS_ORIGINS") or "").strip()
    if not raw:
        # safe default for local dev; you can also choose to raise instead
        return ["http://localhost:5173"]

    # JSON array support
    if raw.startswith("["):
        try:
            val = json.loads(raw)
            if isinstance(val, list) and all(isinstance(x, str) for x in val):
                return [x.strip() for x in val if x.strip()]
        except Exception:
            pass  # fall back to CSV parsing

    # CSV parsing
    return [x.strip() for x in raw.split(",") if x.strip()]

# --- app ---
app = FastAPI(title="Amharic Normalization API v0")

# --- models ---
class NormalizeRequest(BaseModel):
    text: str = Field(
        ...,
        example="selam! EnkWan dehna meTu!"
    )
    options: Optional[Dict[str, Any]] = Field(
        default={
            "latin_mode": "auto",
            "return_alternatives": True,
            "max_alternatives": 5,
            "habit_strength": 0.85
        },
        example={
            "latin_mode": "auto",
            "return_alternatives": True,
            "max_alternatives": 5,
            "habit_strength": 0.85
        }
    )

# --- CORS (env-driven) ---
allow_origins = _get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- new lexicon endpoint ---
LEXICON_V1 = ROOT / "resources" / "am_ui_v1.json"

@app.get("/ui-lexicon")
def ui_lexicon(v: int = 1):
    if v != 1:
        raise HTTPException(
            status_code=400,
            detail={"error": "unsupported version", "supported": [1]},
        )
    return json.loads(LEXICON_V1.read_text(encoding="utf-8"))

# --- existing normalize endpoint ---
@app.post("/normalize")
def normalize_endpoint(req: NormalizeRequest):
    out = normalize(req.text, req.options)

    opts = req.options or {}
    if opts.get("return_latin_std"):
        latin = car_to_latin_std(out["car"])
        out["latin_std"] = ethiopic_punct_to_ascii(latin)

    return out

class ResolveUiRequest(BaseModel):
    text: str = Field(
        ...,
        example="ui.auth.login"
    )
    latin_mode: Optional[str] = Field(
        default="auto",
        example="auto"
    )

@app.post("/resolve-ui")
def resolve_ui(req: ResolveUiRequest):
    if req.latin_mode not in (None, "auto", "strict"):
        raise HTTPException(
            status_code=400,
            detail="latin_mode must be 'auto' or 'strict'",
        )

    item = resolve_ui_key(req.text, latin_mode=req.latin_mode or "auto")
    if item is None:
        return {"resolved": False}

    return {
        "resolved": True,
        "key": item["key"],
        "am": item["am"],
        "category": item.get("category"),
    }
