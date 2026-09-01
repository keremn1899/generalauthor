# jsonlib v3 migration reference

The v2 `loads(..., allow_comments=True, parse_float=Decimal)` convenience call is
removed. Equivalent v3 decoding is:

```python
Decoder(allow_comments=True, number_mode="decimal").decode(payload)
```

The v3 default rejects comments and uses binary floating-point numbers.

For encoding, `Encoder(canonical_keys=True, decimal_mode="decimal-string")`
preserves canonical object-key order and emits Decimal values as quoted strings.

