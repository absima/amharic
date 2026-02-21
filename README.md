# Amharic Normalization & Canonical Representation (AN / CAR) --- v0

This project provides a deterministic, reversible infrastructure layer
for Amharic text processing.

It consists of:

-   **CAR (Canonical Amharic Representation)** --- strict 1→1 encoding
    of Ethiopic script
-   **AN (Amharic Normalizer v0)** --- ambiguity-aware normalization
    pipeline
-   **UI Resolver (v1)** --- deterministic UI lexicon contract layer
-   **FastAPI service wrapper** --- deployable API interface

------------------------------------------------------------------------

## 1. Project Structure

-   `am_normalizer/` --- Core normalization and canonical encoding
    engine
-   `api/` --- FastAPI wrapper exposing HTTP endpoints
-   `tables/` --- Authoritative mapping tables
-   `resources/` --- UI lexicon and alias data
-   `tests/` --- Conformance and regression tests
-   `spec/` --- Formal specifications and design rationale

------------------------------------------------------------------------

## 2. Core Concepts

### CAR (Canonical Representation)

CAR encodes each Ethiopic character as:

    <base><variant?><order>

Where:

-   `base` = consonant family (e.g. `m`, `sh`, `t'`)
-   `variant` = optional family digit (for historically distinct sets)
-   `order` = Ethiopic order (1--7; 8 only allowlisted)

Examples:

  Ethiopic   CAR
  ---------- ---------
  ምን         m6n6
  የት         y1t6
  ሲመጣ        s3m1t'4

CAR is fully reversible and contains no ambiguity.

------------------------------------------------------------------------

### AN-v0 (Normalizer)

The normalizer converts:

-   Ethiopic Unicode
-   Latin transliteration (auto or strict)
-   Mixed input

into canonical CAR.

Features:

-   Ambiguity-aware decoding
-   Confidence scoring
-   Explicit alternatives (never silent guessing)
-   Optional Latin-Std reversible output

------------------------------------------------------------------------

### UI Resolver (v1)

The UI resolver maps user input to pinned UI lexicon entries.

Resolution order:

1.  Direct canonical key match (e.g., `ui.auth.login`)
2.  Alias match
3.  Normalization → Amharic match
4.  Normalization → CAR match

It guarantees deterministic mapping for UI contracts.

------------------------------------------------------------------------

## 3. Installation

From repository root:

``` bash
pip install -e .
pip install -r api/requirements.txt
```

------------------------------------------------------------------------

## 4. Running the API Locally

``` bash
uvicorn api.app:app --reload
```

API will be available at:

    http://127.0.0.1:8000

Interactive docs:

    http://127.0.0.1:8000/docs

------------------------------------------------------------------------

## 5. API Endpoints

### GET /ui-lexicon

Returns the pinned UI lexicon.

Test:

``` bash
curl http://127.0.0.1:8000/ui-lexicon
```

------------------------------------------------------------------------

### POST /normalize

Normalizes text into Amharic + CAR.

Example:

``` bash
curl -X POST http://127.0.0.1:8000/normalize   -H "Content-Type: application/json"   -d '{"text":"selam","options":{"latin_mode":"auto"}}'
```

Response includes:

-   `text_am`
-   `car`
-   `confidence`
-   `alternatives` (if requested)

------------------------------------------------------------------------

### POST /resolve-ui

Resolves UI keys or aliases to pinned lexicon entries.

Example:

``` bash
curl -X POST http://127.0.0.1:8000/resolve-ui   -H "Content-Type: application/json"   -d '{"text":"ui.auth.login"}'
```

Expected response:

``` json
{
  "resolved": true,
  "key": "ui.auth.login",
  "am": "ይግቡ",
  "category": "auth"
}
```

------------------------------------------------------------------------

## 6. Environment Variables

`CORS_ORIGINS` supports:

-   Comma-separated:

        CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

-   JSON array:

        CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

------------------------------------------------------------------------

## 7. Testing

Run full test suite:

``` bash
python -m pytest
```

All tests must pass before tagging releases.

------------------------------------------------------------------------

## 8. License

MIT License (2025 Simachew Mengiste)

------------------------------------------------------------------------

## Status

-   CAR v0 --- complete and bijective
-   AN v0 --- stable
-   UI Resolver v1 --- deterministic and pinned
-   API wrapper --- deployable

This project forms a foundational infrastructure layer for Amharic NLP,
localization, and AI-assisted writing systems.
