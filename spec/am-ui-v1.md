# AM-UI-v1 — Amharic Web-UI Lexicon (CAR-pinned)

## 1. Purpose
AM-UI-v1 defines a small, formal, non-gendered set of Amharic UI phrases for web applications.

It is designed to be:
- stable (keyed, versioned)
- deterministic (no silent drift)
- compatible with CAR v0 canonicalization
- regression-testable (CAR is pinned per entry)

AM-UI-v1 is a lexicon, not a translation system.

---

## 2. File
`resources/am_ui_v1.json`

---

## 3. Data model

### 3.1 Top-level schema
- `version` (string): must be `"am-ui-v1"`
- `locale` (string): e.g. `"am-ET"`
- `items` (array): list of UI phrases

### 3.2 Item schema
Each item MUST contain:
- `key` (string): stable identifier (namespaced)
- `am` (string): Ethiopic UI phrase (display string)
- `car` (string): CAR v0 canonical form (pinned)
- `category` (string): semantic group (e.g., `auth`, `form`, `status`, `error`, `nav`, `common`)

Example:

{
  "key": "ui.auth.login",
  "am": "ይግቡ",
  "car": "<CAR-V0>",
  "category": "auth"
}

---

## 4. Normative constraints

### 4.1 Stability
- `key` MUST be stable across releases.
- Removing or renaming keys is a breaking change (requires a new major version).

### 4.2 Determinism
Given the normalizer `normalize(text)`:
- `normalize(am).text_am` MUST equal the exact stored `am`.
- `normalize(am).car` MUST equal the exact stored `car`.

These constraints are enforced by tests.

### 4.3 Register and tone
- `am` MUST use polite, non-gendered forms suitable for web UI.
- Avoid gender-marked address forms.
- Avoid colloquial or ambiguous phrasing.

### 4.4 Uniqueness
- `key` MUST be unique across items.
- `car` SHOULD be unique across items.

---

## 5. Versioning
- The lexicon uses semantic versioning via the `version` field.
- `am-ui-v1` is a stable contract.

---

## 6. Recommended key conventions
- Prefix: `ui.`
- Domain grouping: `auth`, `form`, `status`, `error`, `nav`, `common`

---

## 7. Testing requirements (normative)
Tests MUST enforce:
- round-trip stability
- CAR stability
- minimum confidence threshold for Ethiopic-only UI strings

---

## 8. Non-goals
AM-UI-v1 does NOT:
- perform translation
- provide fuzzy matching
- infer intent
- guess between ambiguous alternatives
