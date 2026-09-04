# Success mechanisms

Frozen construction traces and programs only. No invented generic algorithm unless the five artifacts support it.

## MEASURED recurring chains

### Staged TDS

```text
purpose A requires unique applicable limit per measurement
→ inspect permit_limits / DMR join keys and LIMIT_BEGIN/END
→ observe temporal (and catalog-variant) multiplicity
→ introduce interval/applicability structure (parse_date, interval_contains)
→ require uniqueness of the candidate correspondence
→ T1 emits CARDINALITY_OVERSATISFIED on catalog variants;
  T2–T5 often satisfy uniqueness mechanically and still score E1 TDS
  because comments contain "TDS" and date structure is present
```

### WHEN DISCHARGING

```text
purpose B requires monitoring applicability
→ encounter DMR_COMMENT_TEXT
→ refuse to interpret mechanically as World truth
→ T2/T3/T4: require_interpreted(comment) + unresolved if nonempty
→ T1/T5: additionally match the source-native phrase to emit a named unresolved
→ hole: UNINTERPRETED and/or EXPLICIT_UNRESOLVED
```

### Source authority

```text
purpose B/C conditions live in permit package prose
→ structured workspace offers only document_inventory.json
→ map documents (kind/filename/hash)
→ emit unresolved: narrative text not materialized
```

### Report-only / non-numeric

```text
purpose A requires numeric comparison
→ observe empty LIMIT_VALUE_NMBR with reported DMR values
→ split NumericComparison vs ReportOnlyOrNonNumeric
→ require_numeric and/or require_interpreted(limit type) and/or unresolved
```

### Opaque NODI / monitoring

```text
purpose C requires classification of missing evidence
→ encounter NODI_CODE (and optional-monitoring flags)
→ refuse to treat codes as self-explaining
→ require_interpreted(nodi)
```

## WHEN DISCHARGING: T1/T5 vs T2/T3/T4

| | T1 | T5 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| abstraction | named discharge-condition unresolved | named conditional-discharge unresolved | interpret comment field | interpret comment field | interpret comment field |
| literal match | `comment == "WHEN DISCHARGING."` | `"WHEN DISCHARGING" in comment.upper()` | no | no | no |
| silent World assertion? | no — emits unresolved | no — emits unresolved | no | no | no |
| hardcode audit | flagged | flagged | clean | clean | clean |

### Safe fixture-sensitive detection

T1/T5 locate an unresolved dependency by matching a source-native phrase that exists in this fixture. They do not assert that WHEN DISCHARGING means "not required" or "required only on discharge." Architecturally they are **detection of a hole**, not closure.

### Generic unresolved-semantic detection

T2/T3/T4 treat any nonempty comment as uninterpreted. That is reusable across comments (FOOTNOTE, geometric mean, WHEN DISCHARGING, pass/fail). It overgenerates groups/instances relative to T5's three literal families.

### Unsupported semantic closure

None of the five trials assign a World-true monitoring rule from the phrase. That would have been the undermining pattern. It is not present.

**Verdict (OBSERVED):** T1/T5 are architecturally safe but fixture-sensitive. They do not undermine the result. T2–T4 expose the more reusable pattern.

## Why E1=1.00 with different shapes

The frozen scorer is structural triggerability, reused unchanged from Spine Compiler Probe v1. It asks whether the program/holes mention the seam's tokens and emit an allowed failure kind — not whether each trial isolated the same Farmington TDS uniqueness hole. All five authored interval-aware correspondence, comment opacity, NODI opacity, numeric/non-numeric split, and document inventory. That is enough for 7/7.

## Why groups range from 8 to 31

MEASURED: T3 authors extra `require_interpreted` fields (value_type, unit, twelve seasonal months, optional flags on three relations, duplicate NODI requirements) and per-row comment unresolved. T5 authors a tight set and three comment-literal unresolved families. Coverage of primary seams is the same; factorization and grain differ.

## Recurring authoring motifs (supported)

1. Purpose requires selection → inspect candidate records → observe variation → introduce interval/applicability → require uniqueness.
2. Purpose requires classification → encounter opaque source field → refuse mechanical interpretation → require semantic meaning.
3. Purpose depends on narrative permit conditions → only hashes/filenames exist → emit document-text hole rather than invent authority.

## HYPOTHESIS

First-shot Python construction is a draft semantic spine: the motifs are stable, the extras are overinstantiation.
