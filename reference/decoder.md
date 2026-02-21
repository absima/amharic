# Decoding CAR -> Ethiopic (reference)

Input: CAR string (tokens may be concatenated)
Output: Unicode Ethiopic text

Token grammar (v0):
- base: [a-z]+ with optional trailing apostrophe
- variant: optional '1' or '2' (only for specific bases)
- order: final digit [1-8]

Stream parsing:
1) Scan left-to-right.
2) When you see a letter-start, read until you reach a digit [1-8] that terminates a token:
   - Order is the last digit.
   - If the char before order is a digit in {1,2}, it is the variant.
   - Everything earlier is the base.
3) Lookup the corresponding Ethiopic letter in tables:
   - orders 1–7: tables/orders.tsv
   - order 8: tables/order8.tsv allowlist only
4) Emit Ethiopic letter; preserve non-token characters (spaces/punctuation) as-is.

Errors:
- Token not matching grammar
- Base+variant not in families.tsv
- Order not in orders.tsv (or not allowlisted for 8)

