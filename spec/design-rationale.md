# Design rationale (CAR v0)

## CAR is not a phonetic romanization
CAR encodes Ethiopic orthography (families + order slots). It is designed for deterministic conversion, indexing, and NLP/OCR pipelines. Human-friendly transliteration is handled in a separate normalization layer.

## Why the order digit is last
Stream parsing becomes deterministic without requiring delimiters between letters (tokens can be concatenated).

## Why variants are optional digits
Most letters do not need variant marking. Only historically distinct families that are commonly merged in modern usage are separated:
- h / h1 / h2
- s / s1
- ts' / ts'1
- a / a1

This keeps canonical strings short while preserving 1→1 mapping.

## Why q for ቀ-family
It is common in Ethiopian informal romanization and is compact and stable for tooling.

## Why apostrophe for ejectives
Ejectives are preserved explicitly (t', ch', p', ts') and remain stable across communities.

## Why order 8 is an allowlist
Ethiopic has more labialized derivatives than Amharic needs day-to-day. v0 keeps scope strictly Amharic-focused while supporting an explicit must-have list.

## Why punctuation is not part of CAR
Punctuation normalization is a separate layer (TNC). CAR maps letters 1→1; punctuation can be preserved or normalized depending on application.

