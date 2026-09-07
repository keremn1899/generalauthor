# Read-surface metrics

Not a token-optimization study. Small sample. Shell-log `join` counts under-count SQL embedded in Python heredocs; Part B `answers.json` `code` fields are the better program record.

## MEASURED

Compact contract: **1176 bytes**. Identical across domains.

### Part A (3 Worlds, 12 questions)

| arm | initial context bytes | contract bytes | mean reads | mean shells | inspect_world calls | catalog_calls | raw-source reads |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A0 | 2622 | 0 | 7.3 | 3.3 | 1.0 | 1.0 | 0 |
| A1 | 3858 | 1176 | 8.3 | 5.3 | 1.0 | 1.3 | 0 |

### Part B (1 World, 3 tasks)

| arm | initial context bytes | contract bytes | mean reads | mean shells | inspect_world calls | raw-source reads |
| --- | --- | --- | --- | --- | --- | --- |
| A0 | 1877 | 0 | 6.8 | 4.3 | 1.0 | 0 |
| A1 | 3109 | 1176 | 7.8 | 3.8 | 1.0 | 0 |

Contract amplification (contract bytes / initial context without contract):

```text
Part A: 1176 / 2622 ≈ 0.45
Part B: 1176 / 1877 ≈ 0.63
```

Vocabulary/introspection vs dynamic state: every episode called `inspect_world(s).py` once, then queried sqlite. A1 did **not** reduce catalog/describe work.

World sqlite hashes after every episode match `evaluator_only/freeze.json`. Isolation preflight `ok`. Isolation leaks: none. Composer 2.5 on all 18 runs.

## OBSERVED

A1 pays ~1.2 KB of stable orientation and slightly **more** file reads (they open CONTRACT.md). It does not replace `inspect_world` or cut SQL. The contract is cheap relative to dumping three Worlds; it is not an introspection-eliminating ABI.

Part B programs used SQL JOIN heavily (29/36 codes) despite shell-log join_count ≈ 0–0.2. Measure programs from returned code, not from truncated shell strings.

## HYPOTHESIS

A small stable contract is inexpensive. On this sample it does not remove orientation work. Its value, if any, is reasoning (Part A grain), not catalog compression.
