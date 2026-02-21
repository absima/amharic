# Encoding Ethiopic -> CAR (reference)

Input: Unicode Ethiopic text (Amharic-focused)
Output: CAR string

Algorithm:
1) For each character c in input:
   - If c is an Ethiopic letter supported by tables/orders.tsv or tables/order8.tsv:
     a) Find its (base, variant, order) triple.
     b) Emit token: base + variant(if exists) + order
   - Else:
     - Emit c unchanged (whitespace/punctuation) OR apply punctuation normalization if your pipeline uses TNC.

Constraints:
- Only allow order=8 if the character appears in tables/order8.tsv.
- If a character is Ethiopic but unsupported, error or pass-through depending on your use case (validator should error).

