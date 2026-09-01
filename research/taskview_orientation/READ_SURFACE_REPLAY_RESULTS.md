# TaskView read-surface replay results

**Status:** offline, zero inference. Sealed campaign `taskview-orientation-stage1-cursor-v01-v4-searchfix`.
**Participant / provider calls:** `0`.

This is a counterfactual payload/accounting study. It does not claim that
participant behavior would remain unchanged under a new surface.

Serializer freeze:

```text
serializer_id  taskview-read-surface-replay-serializers-v1
config_sha256  0a184d29a6fd5acfe71f79e9bfe10266d3810be0f418f64871a1fb81721b8215
module_sha256  79155c5c6b665d93caa4d5f841c00e3ce86eab1806fd41d2972572929d3e6902
```

Sealed identity (unchanged):

```text
campaign_seal_sha256  15ca653bd7b66acee5b1be4c6da9232b9f63ba9f44b7e1e48b9c5c0c292d9131
manifest_sha256       6108435143ff33f9806951059f114221e85e8177652e64abfecb3a3fa104a1aa
```

SQL ledger facts (must match the preregistered 111-call corpus):

```text
{
  "aggregate": 0,
  "cte": 0,
  "filtered_calls": 16,
  "join": 0,
  "order_limit_variants": 6,
  "plain_enumerations": 89,
  "query_sql_calls": 111,
  "query_sql_error_calls": 0,
  "select_star": 111,
  "set_operation": 0,
  "single_relation": 111,
  "subquery": 0,
  "unparsed": 0
}
```

Budgets `RAW_O_post - TASKVIEW_repository_O_post`: `{1: 4534, 2: 10964, 3: 8329, 4: 3050}`.

Net delta = acquisition-inclusive TaskView read bytes − budget.
Negative is net-positive economics. Post-phase-1 bytes are also stored on each
summary for historical comparability and do not hide initialization contracts.

Candidate B's post-phase-1 net is negative in 2/4 replicates. That is the
init-placement artifact this admission rule exists to block: the contract is
charged in acquisition-inclusive totals, never dropped.

## Table 1 — Trajectory-preserving (acquisition-inclusive)

| candidate | R1 net Δ | R2 net Δ | R3 net Δ | R4 net Δ | median | wins | safety | admission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 15,778 | 9,200 | 12,742 | 18,418 | 14260 | 0 | PASS | DEPRIORITIZE |
| B | 7,406 | 3,439 | 4,370 | 10,046 | 5888 | 0 | PASS | DEPRIORITIZE |
| C | 7,904 | 3,937 | 4,868 | 10,544 | 6386 | 0 | PASS | DEPRIORITIZE |
| D | 9,093 | 5,412 | 6,053 | 11,425 | 7573 | 0 | PASS | DEPRIORITIZE |
| E | 7,685 | 4,027 | 5,438 | 10,790 | 6561.5 | 0 | PASS | DEPRIORITIZE |
| F | 18,547 | 12,045 | 15,762 | 21,571 | 17154.5 | 0 | PASS | DEPRIORITIZE |

## Table 2 — Mechanical dedup floor

| candidate | R1 net Δ | R2 net Δ | R3 net Δ | R4 net Δ | median | wins | safety | admission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 9,429 | 5,594 | 6,710 | 12,657 | 8069.5 | 0 | PASS | DEPRIORITIZE |
| B | 6,279 | 2,444 | 3,560 | 9,507 | 4919.5 | 0 | PASS | DEPRIORITIZE |
| C | 6,777 | 2,942 | 4,058 | 10,005 | 5417.5 | 0 | PASS | DEPRIORITIZE |
| D | 7,861 | 4,336 | 5,153 | 10,835 | 6507 | 0 | PASS | DEPRIORITIZE |
| E | 7,401 | 3,863 | 5,042 | 10,790 | 6221.5 | 0 | PASS | DEPRIORITIZE |
| F | 11,952 | 8,413 | 9,230 | 15,640 | 10591 | 0 | PASS | DEPRIORITIZE |

## Table 3 — Acquisition decomposition (median trajectory-preserving)

| candidate | contract | tool schema | state | epistemic | grounding | maintenance | total |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0 | 866 | 3124 | 13781 | 0 | 1015.5 | 20691.5 |
| B | 2034 | 904 | 3124 | 3797 | 0 | 1015.5 | 12897.5 |
| C | 2034 | 1402 | 3124 | 3797 | 0 | 1015.5 | 13395.5 |
| D | 0 | 1026 | 3124 | 6940.5 | 0 | 1015.5 | 14428.5 |
| E | 2034 | 1091 | 2556 | 4570 | 0 | 1015.5 | 13803.5 |
| F | 0 | 995 | 2707.5 | 16920.5 | 0 | 1015.5 | 23586 |

## Table 4 — Per-candidate savings source (pairwise, not additive)

| contrast | median byte Δ | note |
| --- | --- | --- |
| contract_lifetime_B_minus_A | -7794 | stable contract once vs repeated catalog describe; SQL held fixed |
| request_language_C_minus_B | 498 | simple access vs SQL with identical row serializer |
| auto_context_D_minus_A | -6263 | first-use cards replace catalog; SQL retained |
| bundling_E_minus_B | 906 | oracle phase-union bundle vs per-call SQL under the same contract |
| selector_E1_minus_E | 281.5 | one extra relation in the oracle bundle |
| selector_Eall_minus_E | 6602.5 | all-relations bundle vs observed-union oracle bundle |
| conditional_F_minus_A | 2894.5 | not_modified on unchanged query+revision; describes retained |
| state_dedup_A_floor_minus_A | -5318.5 | mechanical unique (query, revision) floor on pull+SQL |
| state_dedup_B_floor_minus_B | -674.5 | mechanical unique delivery under stable contract |
| state_dedup_F_floor_minus_F | -5461.5 | mechanical floor beyond trajectory-preserving not_modified |

## Behavioral-greed baselines (historical ledger)

- R1: breadth/phase={'1': 10, '2': 5, '3': 5, '4': 2, '5': 5}, queries=29, episode refresh=0.58, exact reread=0.31, rows=36/20, full-scan=0.86, filter=0.14
- R2: breadth/phase={'1': 11, '2': 4, '3': 4, '4': 3, '5': 4}, queries=28, episode refresh=0.53, exact reread=0.25, rows=40/26, full-scan=0.86, filter=0.04
- R3: breadth/phase={'1': 9, '2': 4, '3': 4, '4': 3, '5': 5}, queries=27, episode refresh=0.50, exact reread=0.26, rows=32/20, full-scan=0.85, filter=0.15
- R4: breadth/phase={'1': 6, '2': 6, '3': 4, '4': 2, '5': 5}, queries=27, episode refresh=0.42, exact reread=0.15, rows=30/18, full-scan=0.63, filter=0.26

## Specific questions

**Q1.** No. Stable contract + unchanged SQL (candidate B) does not cross net zero on trajectory-preserving acquisition-inclusive replay (median 5888.0, wins 0/4, admission=DEPRIORITIZE).

**Q2.** No material response-side change: median dynamic-row bytes are identical (B=3124, C=3124). The 498 acquisition-inclusive gap is tool-schema/envelope (1402 vs 904), not query-language response cost. Safety PASS.

**Q3.** Revision-sensitive first-use context (D) median net 7573.0 versus B 5888.0 (difference 1685). This is automatic relation-card delivery, not a live relevance classifier.

**Q4.** Repeated unchanged-state reads: F vs A median net difference 2894; B mechanical floor median 4919.5 versus B trajectory-preserving 5888.0. These floors are not behavioral predictions.

**Q5.** Observed-union bundle E median net 6561.5 (admission DEPRIORITIZE); +1 extra relation 6948; all-relations 13134. E is an oracle accounting lower bound, not a prospective selector.

**Q6.** None.

**Q7.** Candidate B has the best combination of trajectory-preserving economics, safety, and mechanism cost among the frozen set. This is not a v0.2 selection.

## A. Replay validity

All four TASKVIEW trajectories reconstructed: **yes**.

None. All four TASKVIEW trajectories reconstructed.

## B. Candidate ranking

Trajectory-preserving acquisition-inclusive median net delta, then safety, then added mechanism:

| candidate | R1 net Δ | R2 net Δ | R3 net Δ | R4 net Δ | median | wins | safety | admission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 7,406 | 3,439 | 4,370 | 10,046 | 5888 | 0 | PASS | DEPRIORITIZE |
| C | 7,904 | 3,937 | 4,868 | 10,544 | 6386 | 0 | PASS | DEPRIORITIZE |
| E | 7,685 | 4,027 | 5,438 | 10,790 | 6561.5 | 0 | PASS | DEPRIORITIZE |
| D | 9,093 | 5,412 | 6,053 | 11,425 | 7573 | 0 | PASS | DEPRIORITIZE |
| A | 15,778 | 9,200 | 12,742 | 18,418 | 14260 | 0 | PASS | DEPRIORITIZE |
| F | 18,547 | 12,045 | 15,762 | 21,571 | 17154.5 | 0 | PASS | DEPRIORITIZE |

Mechanical floor:

| candidate | R1 net Δ | R2 net Δ | R3 net Δ | R4 net Δ | median | wins | safety | admission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B | 6,279 | 2,444 | 3,560 | 9,507 | 4919.5 | 0 | PASS | DEPRIORITIZE |
| C | 6,777 | 2,942 | 4,058 | 10,005 | 5417.5 | 0 | PASS | DEPRIORITIZE |
| E | 7,401 | 3,863 | 5,042 | 10,790 | 6221.5 | 0 | PASS | DEPRIORITIZE |
| D | 7,861 | 4,336 | 5,153 | 10,835 | 6507 | 0 | PASS | DEPRIORITIZE |
| A | 9,429 | 5,594 | 6,710 | 12,657 | 8069.5 | 0 | PASS | DEPRIORITIZE |
| F | 11,952 | 8,413 | 9,230 | 15,640 | 10591 | 0 | PASS | DEPRIORITIZE |

## C. Live shortlist

Recommend at most three future live contrasts, not a v0.2 architecture:

1. fresh pull+SQL (A / T0)
2. stable pushed contract+SQL (B / T1)
3. revision-triggered epistemic cards on SQL (D / T3)

Do not implement a live arm from this report. Do not authorize participant inference.

## D. Next causal uncertainty

Whether a stable, schema-versioned contract actually removes catalog rediscovery
behavior in a live participant, or whether agents continue to re-pull vocabulary
and re-read unchanged relations even when the contract is already in context.

That question cannot be answered by offline payload replay.  Section E says
how large a live retrieval-strategy shift would have to be before B could
matter economically.

## E. B behavioral headroom (not valid counterfactual behavior)

Question: how much of the observed B trajectory has to change for
acquisition-inclusive TaskView bytes to fall below the orientation budget?

These rows are an accounting break-even map.  They are not predictions that a
live agent would drop describes, narrow SQL, or keep epistemic checks in this
combination.

Matcher: citation-stripped phase-answer substring match on returned cells,
referent local-names (length ≥ 4), and
relation names.  Shared identifiers over-include; prose without those tokens
under-includes.  Oracle-required relations are a frozen field→relation
sensitivity, not participant intent.

### E.1 Observed B anatomy vs budget

| pair | budget | B acq | gap | fixed overhead | fixed ≥ budget | redundant describe B | vocab-strip savings | speculative SQL B | contributing SQL B |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 4,534 | 11,940 | 7,406 | 3,766 | no | 559 | 2,749 | 997 | 2,884 |
| 2 | 10,964 | 14,403 | 3,439 | 3,766 | no | 2,615 | 4,805 | 1,429 | 2,715 |
| 3 | 8,329 | 12,699 | 4,370 | 3,853 | no | 1,593 | 3,783 | 1,077 | 2,298 |
| 4 | 3,050 | 13,096 | 10,046 | 3,853 | yes | 2,165 | 4,355 | 573 | 2,627 |

Gap remaining after contract-redundant vocabulary is stripped from targeted
describes:

| pair | gap after vocab strip | speculative SQL that must vanish | all SQL that must vanish | zero from describe cut alone | zero if all speculative SQL also dropped | still short after zero SQL |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 4,657 | n/a | n/a | no | no | yes |
| 2 | -1,366 | n/a | n/a | yes | yes | no |
| 3 | 587 | 55% | 17% | no | yes | no |
| 4 | 5,691 | n/a | n/a | no | no | yes |

### E.2 Break-even scenarios

Negative net Δ is an economic win.  Conservative rows keep `describe(why)`,
compact completeness/currentness remainders, and post-mutation derived reads.

| scenario | R1 net Δ | R2 net Δ | R3 net Δ | R4 net Δ | median | wins |
| --- | --- | --- | --- | --- | --- | --- |
| B_as_observed | 7,406 | 3,439 | 4,370 | 10,046 | 5888 | 0 |
| drop_contract_redundant_describe | 4,657 | -1,366 | 587 | 5,691 | 2622 | 1 |
| answer_supported_breadth_only | 6,409 | 2,010 | 3,293 | 9,473 | 4851 | 0 |
| redundant_describe_and_contributing_breadth | 3,660 | -2,795 | -490 | 5,118 | 1585 | 2 |
| both_epistemic_conservative | 3,660 | -2,576 | -490 | 5,152 | 1585 | 2 |
| redundant_describe_plus_25pct_speculative_cut | 4,255 | -1,720 | 233 | 5,519 | 2244 | 1 |
| all_relation_describe_gone_plus_half_breadth | 1,405 | -5,188 | -2,725 | 2,784 | -660 | 2 |
| fixed_overhead_only | -768 | -7,198 | -4,476 | 803 | -2622 | 3 |

- `B_as_observed`: Trajectory-preserving B. Not a counterfactual.
- `drop_contract_redundant_describe`: Contract-redundant targeted describes disappear; mixed describes compact to epistemic remainder; SQL unchanged.
- `answer_supported_breadth_only`: Keep SQL only for relations whose returned cells or relation name appear in the citation-stripped phase answer.
- `redundant_describe_and_contributing_breadth`: Both cuts. Completeness scans that did not mark the answer are dropped.
- `both_epistemic_conservative`: Both cuts, but why-describes, compact completeness/currentness, and post-mutation derived reads stay.
- `redundant_describe_plus_25pct_speculative_cut`: Drop contract-redundant describes and the largest speculative (phase, relation) groups until ≤75% of speculative SQL bytes remain.
- `all_relation_describe_gone_plus_half_breadth`: Harsh bound: every relation describe gone; keep half the queried (phase, relation) pairs, preferring answer-supported ones.
- `fixed_overhead_only`: Lower bound under B: contract + tool schema + assertion/rerun. No TaskView reads.

### E.3 Combination required to cross zero in each pair

- R1: first named combo that crosses zero is `fixed_overhead_only` (net Δ -768).
- R2: first named combo that crosses zero is `drop_contract_redundant_describe` (net Δ -1366).
- R3: first named combo that crosses zero is `both_epistemic_conservative` (net Δ -490).
- R4: cannot cross zero under B (fixed overhead net Δ 803). B fixed overhead (contract + tool schema + assertion/rerun) already exceeds the orientation budget

**Economic-headroom label:** `REQUIRES_NEAR_ZERO_READS`.

Only the no-read fixed-overhead floor reaches 3/4. A modest describe-plus-25%-speculative cut does not, and neither does dropping every relation describe and halving breadth. Do not buy inference expecting T1 to produce net-positive economics. If a live T0/T1 contrast happens, its only remaining justification is a retrieval-strategy measurement (Δ breadth, Δ introspection, Δ state queries, Δ repository exploration) with epistemic caution intact.

Modest bar (redundant describe + 25% speculative-breadth cut):
1/4.
Both cuts with epistemic checks kept: 2/4.
Harsh bar (all relation describe gone + half breadth):
2/4.
Fixed-overhead floor: 3/4.
Pairs that cannot cross zero under B at all:
1/4.

If a live T0/T1 contrast is ever authorized, its purpose is not catalog-byte
savings.  Measure Δ relation breadth, Δ targeted introspection, Δ state
queries, and Δ repository exploration, and check that epistemic caution stays
intact.  If those barely move, flat broad retrieval is the preferred strategy
at this scale.  If they collapse, interface uncertainty was causing
overconsumption of TaskView and the repository.

Do not implement a live arm from this report. Do not authorize participant inference.
