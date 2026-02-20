# CAR (Canonical Amharic Representation) — v0

CAR is a deterministic, reversible ASCII encoding for Amharic Ethiopic text.

## Why CAR
- Eliminates ambiguous mappings by representing Ethiopic orthography directly (not phonetic guesses).
- Enables reliable pipelines for:
  - website translation pre/post-processing
  - AI writing assistance (validation + cleanup)
  - OCR post-correction
  - dictionary and corpus building
- Separates concerns:
  - **CAR**: strict 1→1 canonical encoding
  - **Normalizer** (future): many→1 mapping from messy Latin/typed input into CAR

## Core idea
Each Ethiopic letter is encoded as:
  <base><variant?><order>

- base: letters (and optional ejective apostrophe)
- variant: optional (only for specific historically distinct families)
- order: final digit 1–8 (8 is allowlisted /wa/ forms only)

Examples:
- ምን  -> m6n6
- የት  -> y1t6
- ሲመጣ -> s3m1t'4
- ስመጣ -> s6m1t'4

## Files
- spec/car-v0.md : normative rules
- tables/*.tsv   : authoritative mappings
- tests/*.json   : conformance tests
- tools/*.py     : reference encoder/decoder/validator

## Status
v0 focuses on Amharic and includes only explicitly allowlisted order-8 letters used in practice.

