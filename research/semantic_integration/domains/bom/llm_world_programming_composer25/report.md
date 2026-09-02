# Composer 2.5 model substitution on frozen RAW vs WORLD

Experiment `bom-llm-world-programming-composer25`.
Manifest fingerprint: `sha256:3872dbc734ac8f1440bac78a17cc7e37ba185e1471823b1778c6bdb33ae6e02d`.
Predecessor: `bom-llm-world-programming-v3` (`sha256:b88da582b1f1a4477c47d444caf5f12945649501f340e4e6ae70906e0e1404f4`).
Provider/model calls: **20**. No further inference after this report.

The experimental variable is the model. Tasks A/B, prompts, RAW sources, compiled World, obligations, expected outputs, scorer, failure taxonomy, budget, and bwrap isolation are the frozen v3 protocol.

Model: `composer-2.5` (stream-json reports `Composer 2.5`). Adapter: `cursor-agent-bwrap-isolated-workspace-agent-composer25`. Nested Cursor sandbox disabled. Live workspaces under `/tmp/world-experiment/bom-llm-world-programming-composer25`.

---

## 1. Exact success

| Condition | Pass | Rate | Wilson 95% |
|---|---:|---:|---|
| RAW | **1/10** | 10% | [0.02, 0.40] |
| WORLD | **10/10** | 100% | [0.72, 1.00] |

| Cell | Pass |
|---|---:|
| RAW A | 1/5 |
| RAW B | 0/5 |
| WORLD A | 5/5 |
| WORLD B | 5/5 |

Wilson intervals do not overlap. Two-sided Fisher exact on the 2×2 table is *p* ≈ 1.2×10⁻⁴. All 20 programs executed. 0 timeouts.

---

## 2. What failed

| Class | Count | Where |
|---|---:|---|
| `CONTEXT_MATCHING` | 7 | RAW A 001, 002, 004, 005; RAW B 001, 003, 005 |
| `SEMANTIC_ACCEPTANCE` | 2 | RAW B 002, 004 |
| WORLD | 0 | — |
| `UNKNOWN_AS_FALSE` | 0 | — |

RAW A 001/002/004/005 omitted `context:indoor_panel` and emitted only note-stated candidate/context pairs.

RAW A 003 passed. Indoor X110/X160 is `unresolved` / `UNRESOLVED`.

RAW B 001/003/005 omitted indoor. RAW B 004 constructed indoor X110/X160 but labeled `not_established` with `semantic_acceptance` under `leaves_viability_uncertain` and empty `prevents_viability`. RAW B 002’s first indoor case is X160/X100 `not_established`.

WORLD A and WORLD B had no failures. Indoor X110/X160 is `unresolved` in all ten WORLD programs.

---

## 3. Isolation

Physical isolation **held**.

- Isolation leak runs: **0/20**
- Preflight ok: **20/20**
- Contaminated Reads of the repository: **0**
- Campaign abort: none

Audit: `scoring/isolation_audit.json`.

---

## 4. Epistemics

`unknown_as_false_count`: **0**.

Indoor X110/X160 was never scored as rejected/false. RAW usually omitted the case or labeled missing acceptance `not_established`. WORLD kept indoor as `unresolved` / `UNRESOLVED`.

`ADJUDICATED_FALSE` remains unrepresentable. The indoor obligation was not resolved.

Task A `support` present: **10/10**.

---

## 5–6. Cost

Monetary usage was **not exposed**. Cursor `result.usage` contained `inputTokens`, `outputTokens`, `cacheReadTokens`, and `cacheWriteTokens`. It did not contain cost, USD, or price keys.

Do not convert those fields into dollars.

| Usage field (sum, 20 runs) | Value |
|---|---:|
| inputTokens | 700672 |
| outputTokens | 187399 |
| cacheReadTokens | 7554258 |
| cacheWriteTokens | 0 |

Total campaign cost: **not measurable**.
Cost by condition: **not measurable**.
Cost per successful program: **not measurable**.

Secondary diagnostics (medians):

| | RAW | WORLD |
|---|---:|---:|
| tool calls | 19 | 22 |
| reads | 6 | 6.5 |
| shell | 4 | 9 |
| python executions (guess) | 4 | 8.5 |
| nonempty LOC | 190.5 | 139.5 |
| source-schema field literals | 9 | 1 |
| World relation references | 5 | 6.5 |

WORLD did not use fewer tool calls. It used fewer source-schema literals and slightly fewer lines. Correctness is the primary result.

---

## 7. Descriptive comparison with frozen GPT-5.6 Sol High v3

Not one randomized experiment. Do not pool.

| | GPT-5.6 Sol High v3 | Composer 2.5 (this campaign) |
|---|---|---|
| RAW A/B | 0/20 | 1/10 |
| WORLD A/B | 18/20 | 10/10 |
| Isolation | held | held |

Both models fail RAW (case construction and missing-acceptance labeling) and succeed WORLD at a high rate on this fixture. Composer WORLD was 10/10; Sol WORLD was 18/20 with two cartesian/join losses on A.

That is consistent with semantic compilation substituting for some downstream model capability on this benchmark: a cheaper model still programs the compiled World at high exact success while remaining near-floor on the equivalent RAW sources. It does not measure construction cost, other domains, or Task C.

---

## 8. Untested

- Task C
- Other domains and larger worlds
- Construction cost of the World vs programming savings
- Other models besides this Composer 2.5 cell and the frozen Sol v3 cell
- Monetary cost
- `ADJUDICATED_FALSE`

---

## MEASURED

- Composer RAW **1/10**; WORLD **10/10**.
- Per-task: RAW A 1/5, RAW B 0/5, WORLD A 5/5, WORLD B 5/5.
- Failure classes: `CONTEXT_MATCHING` 7, `SEMANTIC_ACCEPTANCE` 2.
- `UNKNOWN_AS_FALSE`: 0.
- Isolation leaks: 0.
- Monetary cost: not exposed.
- All 20 saved programs executed.

## OBSERVED

- Isolation held for the full 20-run protocol.
- RAW failures are the same two modes as Sol v3: omitted indoor, or `not_established` instead of `unresolved`.
- WORLD programs classified indoor X110/X160 as `unresolved` using compiled relations plus obligations.
- Cursor did not report dollars. Token/cache fields were recorded and not priced.

## HYPOTHESIS

- On this frozen BOM A/B fixture, compiled World IR lets Composer 2.5 reach high exact programming success that it does not reach against the heterogeneous RAW sources.
- That is a model-substitution claim about downstream programming, not a claim that World construction is cheap or that Python/SQL is the long-term interface.

---

## Stop

All 20 preregistered runs completed. Isolation held. Expected outputs, World IR, WORLD API, prompts, scorer, C0/C1/C2, and the indoor obligation were not modified. Task C, a second domain, and visualization were not run.
