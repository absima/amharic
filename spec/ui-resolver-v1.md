# UI-Resolver-v1 — Deterministic UI Key Resolution

## 1. Purpose
UI-Resolver-v1 defines how user input (Latin, Ethiopic, or mixed) is resolved to an AM-UI-v1 lexicon entry.

Key property:
- The resolver MUST NOT silently guess when input is under-specified.

---

## 2. Files
- Lexicon: `resources/am_ui_v1.json`
- Aliases: `resources/am_ui_aliases_v1.json`
- Implementation: `tools/ui_resolver.py`

---

## 3. Alias model (AM-UI-Aliases-v1)

### 3.1 File schema
`resources/am_ui_aliases_v1.json` contains:
- `version`: must be `"am-ui-aliases-v1"`
- `locale`: e.g. `"am-ET"`
- `items`: list of alias rules

Each alias rule:
- `alias` (string): explicit shortcut text
- `key` (string): AM-UI-v1 key

Example:

{
  "alias": "ygbu",
  "key": "ui.auth.login"
}

---

## 3.2 Alias canonicalization (normative)
Alias input is canonicalized deterministically:
- trim leading/trailing whitespace
- lowercase
- collapse internal whitespace to single spaces

No other transformations are performed.

---

## 4. Resolution order (normative)
Given user input `text`, the resolver attempts resolution in this order:

1. Explicit alias match
2. Normalization → direct Ethiopic match
3. Normalization → unique alternative match
4. Normalization → CAR match (fallback)

If none succeed, resolution fails.

---

## 5. Safety rule (normative)
The resolver MUST NOT:
- guess between alternatives
- perform fuzzy matching
- infer intent

Ambiguous input MUST result in no resolution.

---

## 6. Normalization mode
- Default: `latin_mode = auto`
- Optional: `latin_mode = strict`

---

## 7. Outputs
The resolver returns either:
- the resolved AM-UI-v1 item, or
- `None`

API representations may wrap this in `{resolved, key, am}`.

---

## 8. Testing requirements (normative)
Tests MUST cover:
- alias resolution (including case and whitespace canonicalization)
- normalization-based resolution for at least one known Latin input (`ygbu` → `ui.auth.login`)
- unresolved behavior for non-matching or ambiguous inputs

