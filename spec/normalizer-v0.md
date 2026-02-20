# Amharic Normalizer v0 (AN-v0)

## 1. Purpose
AN-v0 converts noisy user input into:
1) normalized Ethiopic Unicode text (preferred human-facing output)
2) CAR v0 canonical form (machine-facing output)
3) confidence + alternatives when decoding is ambiguous

AN-v0 is designed to support:
- website translation pipelines (pre/post processing)
- AI writing assistance
- search/indexing
- mixed-script user input (Latin + Ethiopic)

AN-v0 is NOT a replacement for CAR. CAR is the strict 1→1 layer.

---

## 2. Inputs and outputs

### 2.1 Input
A Unicode string possibly containing:
- Ethiopic letters (Amharic)
- Latin letters (a-z, A-Z)
- Arabic digits
- punctuation
- whitespace
- mixed spans (common in chat)

### 2.2 Output (contract)
AN-v0 returns an object with:

- text_am: normalized Ethiopic Unicode string (best)
- car: CAR v0 encoding for text_am (letters only; punctuation preserved separately or passed-through)
- confidence: float in [0,1]
- alternatives: list of (text_am, car, confidence, reason) for ambiguous cases
- meta:
  - spans: list of detected spans with script type and decode info
  - warnings: list of warnings (unknown tokens, low confidence, etc.)

AN-v0 MUST NOT silently replace ambiguous Latin input with a single guess without exposing alternatives.

---

## 3. Pipeline overview

AN-v0 executes in stages:

A) Script segmentation
B) Ethiopic normalization (deterministic, safe)
C) Latin decoding (lossy / ambiguous) -> Ethiopic candidates
D) Merge + final CAR encoding
E) Confidence scoring + alternatives

---

## 4. Stage A: Script segmentation

Classify each character:
- ETH: Ethiopic range (U+1200–U+137F plus Ethiopic extended if needed)
- LAT: Latin letters A–Z a–z and apostrophe '
- NUM: digits 0–9
- SEP: whitespace + punctuation

Create spans:
- contiguous ETH spans
- contiguous LAT spans
- keep SEP as separators
- NUM treated as separate spans (passed through; normalization optional)

---

## 5. Stage B: Ethiopic normalization (deterministic)

B1. Whitespace
- Collapse consecutive whitespace to single space
- Trim leading/trailing whitespace

B2. Ethiopic word separator ፡
- Option: convert ፡ to space
- Default v0: convert ፡ -> space

B3. Punctuation
- Default v0: preserve punctuation as-is
- Optional mode: map Ethiopic punctuation to ASCII equivalents per tables/punctuation.tsv

B4. Numerals
- Default v0: preserve digits as-is (Arabic digits)
- Ethiopic numerals: optional future (out of scope v0 unless explicitly needed)

B5. Orthographic variant normalization (CONSERVATIVE)
Default v0: NO automatic merging of historically distinct letters.
(We keep ሀ/ሐ/ኀ, ሰ/ሠ, ጸ/ፀ, አ/ዐ distinct.)
Any optional “merge” mode must be explicitly enabled and documented.

---

## 6. Stage C: Latin decoding (transliteration module)

### 6.1 Philosophy
- Decode Latin to Ethiopic through CAR families + order digits.
- Prefer deterministic decoding when possible.
- When ambiguous, return multiple candidates with confidence.

### 6.2 Tokenization of Latin spans
Split LAT span into tokens:
- words separated by whitespace/punctuation
- keep punctuation as separators

Within each word token, decode left-to-right.

### 6.3 Base recognition (greedy)
Recognize the longest valid base first:
Multi-letter bases:
- ts'  (requires apostrophe) or ts (fallback, lower confidence)
- ch'  (requires apostrophe) or ch (fallback for non-ejective)
- sh
- ch
- ny
- zh
- kh
Single-letter bases:
- h, l, m, r, s, q, b, t, n, k, w, z, y, d, j, g, f, p, v
Ejectives:
- t' (apostrophe required)
- p' (apostrophe required)
- ts' (apostrophe required)
- ch' (apostrophe required)

### 6.4 Variant hints in Latin (optional)
If the user explicitly types variant digits right after a base (e.g., h1, h2, s1, ts'1, a1),
the decoder MUST honor them.

Variant digits allowed (v0): 1, 2

### 6.5 Vowel cue -> order mapping (heuristic)
After base (+ optional variant), the decoder looks for a vowel cue:

- "e" -> order 1
- "u" -> order 2
- "i" -> order 3
- "a" -> order 4
- "ei" -> order 5
- "o" -> order 7
- "wa" -> order 8

No direct ASCII vowel for order 1 or order 6.
Heuristics:
- If no vowel cue found, candidate orders include:
  - order 6 (vowelless) with high prior for consonant-final clusters
  - order 1 as an alternative with lower prior (because many users omit ä/ə)
- AN-v0 MUST surface ambiguity when both yield valid parses.

### 6.6 Strict Latin Mode (STM-v0)

Purpose: deterministic, separator-free transliteration.

Rules:
- Case-sensitive
- No digraph bases allowed
- Each Ethiopic family has a single-letter base

Mapping:
- S → sh (ሸ)
- K → kh (ኸ)
- N → ny (ኘ)
- Z → zh (ዠ)
- C → ch (ቸ)
- C' → ch' (ጨ)
- X → ts' (ጸ)

Token grammar:
<base><variant?><order>

Example:
- ሽን → S6n6
- ስህን → s6h6n6


### 6.7 CAR emission for Latin-decoded candidates
For each decoded letter, emit CAR token:
- <base><variant?><order>

Then decode CAR -> Ethiopic using CAR tables.

### 6.8 Validity checks
A Latin-decoded candidate is valid if:
- every emitted CAR token exists in CAR tables (orders.tsv) OR in order8 allowlist for order=8
- no illegal tokens remain

### 6.9 Scoring (confidence)
Assign a score based on:
+ explicit apostrophes for ejectives (higher confidence)
+ explicit variant digits (higher confidence)
+ vowel cue present (higher confidence)
- relying on order-1 default without cue (penalty)
- relying on ambiguous no-vowel interpretation (penalty when alternatives exist)

Normalize score to [0,1].
Return:
- best candidate as text_am + car + confidence
- top K alternatives (K default 3)

---

## 7. Stage D: Merge decoded spans

Replace each LAT span with decoded Ethiopic best candidate.
Keep ETH spans (after Stage B normalization) unchanged.
Keep punctuation separators.

---

## 8. Stage E: Final CAR encoding

Encode final Ethiopic text into CAR tokens using CAR encoder.
Preserve punctuation/whitespace outside CAR (either pass-through or stored separately).

---

## 9. Error and warning policy

- If a LAT span cannot be decoded, leave it as-is and add warning: "latin_decode_failed"
- If decoding is ambiguous, return alternatives and lower confidence
- Never output Ethiopic characters that are not in CAR tables (unless pass-through mode is explicitly enabled)

---

## 10. Out of scope for v0
- morphological analysis
- dictionary-based disambiguation
- full Tigrinya/Geʽez labialized series
- Ethiopic numeral normalization (unless later required)

---

## 11. Heuristic Profile v0 (Latin decoding)

### 11.1 Goals
- Provide deterministic decoding for a small set of very frequent Amharic function/UI words.
- Avoid morphology/grammar guessing.
- Surface ambiguity with alternatives when input under-specifies Ethiopic orders.

### 11.2 Priority order
1) Exact lexicon match (high confidence, deterministic)
2) CAR-concatenation parsing (e.g., s3m1t'4)
3) Heuristic base+vowel decoding (beam search, ambiguous -> alternatives)
4) Fail-safe: leave Latin span as-is + warning

### 11.3 Lexicon (v0, deterministic)
Latin token (case-insensitive) -> CAR output:

- yet -> y1t6   (የት)
- yete -> y1t5  (የቴ)  [optional; include only if needed later]
- bota -> b7t4  (ቦታ)
- min -> m6n6   (ምን)
- mn  -> m6n6   (ምን)

Implementations MAY extend the lexicon, but v0 MUST keep it small and high-precision.

### 11.4 Ambiguity policy
If the decoder must choose between order-1 and order-6 (or multiple parses):
- Return best candidate + alternatives (top K)
- Reduce confidence
- Do not silently force one interpretation

### 11.5 Non-goals (v0)
The decoder MUST NOT:
- infer person/gender/number from suffix-like Latin endings (e.g., -leh, -sh, -achu) as a hard rule
- invent missing vowels to force a single parse
- produce Ethiopic characters not present in CAR tables

