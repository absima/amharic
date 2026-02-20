# Canonical Amharic Representation (CAR) — v0

## 1. Purpose
CAR defines a deterministic, reversible mapping between Ethiopic (Amharic-focused) characters and an ASCII canonical form.
Design goals:
- 1-to-1 mapping (no uncertain/ambiguous decoding)
- stream-parsable without requiring delimiters between characters
- supports historically distinct families via optional variant digits
- includes only Amharic-relevant /wa/ (order-8) forms (explicit allowlist)

## 2. Token grammar

### 2.1 Canonical letter token
Each Ethiopic letter is encoded as:

  <base><variant?><order>

Where:
- <base> is [a-z]+ and may include a trailing apostrophe `'` for ejectives (e.g., t', ts', ch', p')
- <variant?> is optional and may be '1' or '2' (only for specific bases; see §4)
- <order> is required and is one digit in [1-8]

The last character of a token is ALWAYS the <order> digit.

### 2.2 Token regex (v0)
  ^[a-z]+(')?([12])?[1-8]$

### 2.3 Parsing rule (stream)
Given a stream containing tokens and separators:
- Read from left to right.
- Identify the last digit (1–8) as <order>.
- If the preceding character is a digit (1 or 2), treat it as <variant>.
- Everything before that is <base> (letters + optional apostrophe).

CAR allows concatenating multiple letter tokens with no delimiter:
Example: s3m1t'4

## 3. Orders
Orders 1–7 are the standard Ethiopic order slots for each family.
Order 8 is reserved for the /wa/ form and is included ONLY for an explicit Amharic allowlist (see §6).

Note: Orders are orthographic slots (family tables), not a pronunciation system.

## 4. Variant policy (v0)

Variants exist only for these bases:

### 4.1 h-set (three distinct families)
- h   = ሀ-family
- h1  = ሐ-family
- h2  = ኀ-family

### 4.2 s-set (two distinct families)
- s   = ሰ-family
- s1  = ሠ-family

### 4.3 ts'-set (two distinct families)
- ts'   = ጸ-family
- ts'1  = ፀ-family

### 4.4 a-set (vowel carriers)
- a   = አ-family
- a1  = ዐ-family

All other bases have no variant digit.

## 5. Base inventory (Amharic v0)

Consonant families:
h, l, m, r, s, sh, q, b, t, ch, n, ny, k, kh, w, z, zh, y, d, j, g, f, p, v

Ejectives (apostrophe in base):
t', ch', p', ts'

Vowel carriers:
a

Notes:
- q is reserved for the ቀ-family.
- v (ቨ-family) is included for modern Amharic orthography.

## 6. Order-8 (/wa/) allowlist (Amharic v0)
Order 8 is supported ONLY for the following letter forms:

ሏ ሟ ሧ ሯ ሷ ሿ ቋ ኗ ኋ ኟ ዟ ዧ ዷ ጇ ጧ ጯ ፏ ፗ

These map as defined in tables/order8.tsv.

## 7. Separators and punctuation
CAR v0 treats punctuation and whitespace as separators and keeps them unchanged by default.
(Optionally, a separate normalization layer may map Ethiopic punctuation to ASCII equivalents; see tables/punctuation.tsv.)

## 8. Conformance
An implementation MUST:
- decode every valid CAR token into exactly one Ethiopic letter
- encode every supported Ethiopic letter into exactly one CAR token
- reject tokens outside the grammar and/or not present in the tables
- reject order-8 tokens not present in the allowlist

