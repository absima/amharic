# Amharic Normalization API — v0

## 1. Purpose
This API exposes the AN-v0 normalizer as a stable service.

It converts user input (Ethiopic, Latin, or mixed) into:
- normalized Ethiopic text
- CAR v0 canonical representation
- confidence score
- alternative interpretations when ambiguous

The API MUST NOT silently guess when input is under-specified.

---

## 2. Endpoint overview

### POST /normalize

Normalize Amharic input text.

---

## 3. Request

### 3.1 Headers
- Content-Type: application/json
- Accept: application/json

### 3.2 Request body

```json
{
  "text": "string",
  "options": {
    "latin_mode": "auto | strict",
    "return_alternatives": true,
    "max_alternatives": 3,
    "normalize_punctuation": false
  }
}


