# World IR evidence status

Status is tied to repository experiments, not to the length of the
constructor design. This table is the claim/evidence boundary.

| Claim | Status | Evidence |
|---|---|---|
| source-grounded referents | exercised | `research/taskview_bom/` C1; kernel `SourceObservation` |
| mechanical integration | exercised | C1 adapters, exact identifier seams, retained `spec_conflict` |
| cross-authority relations | exercised | `listing_of`, `rated_voltage`, compatibility/eligibility/conflict derivations |
| sparse frontier | exercised through S100 controlled family | `research/taskview_bom_scaling/` H1; selected records stayed at 8 |
| bounded semantic resolution | exercised on two frozen packets | `domains/bom/c2/results/c2_campaign_report.json`; both ACCEPT, grounded, inserted |
| incremental correctness | exercised | X100 mutation; rerun correct at S1/S10/S100 |
| incremental efficiency | known limitation | `relation_granular_recompute`; 29 → 330 → 3120 tuples recomputed |
| World→multiple-purpose reuse | untested | no second consumer of the same world |
| economic amortization | untested | no token/cost amortization study |
| arbitrary-domain generalization | untested | one controlled parts/BOM family only |

## Construction loop (BOM S1)

```text
C0 frozen semantic world     180 tuples
C1 deterministic compiler    178 tuples; frontier = 2 semantic replacements
C2 bounded adjudicator       2 ACCEPT decisions, packet-grounded
ordinary BASE assert         acceptable_replacement now has those 2 tuples
frontier after C2            0
derived relations            unchanged and current
```

Provider for the successful C2 run: `gpt-5.6-sol-high` via isolated
`cursor-agent --mode ask`. Calls: 2. A prior attempt combined two manufacturer
rows into a non-packet span and was rejected by grounding validation
(`attempts/attempt-0-packet-001-ungrounded.txt`).

`research/taskview_bom_scaling` remains fail-closed
(`SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False`). Live C2 authorization is the
separate two-assertion manifest
`research/semantic_integration/domains/bom/c2/authorized.json`.

## What this is not

No generic entity resolution, embeddings, provider framework, generalized task
compiler, graph UI, or universal ontology was added. TaskView was not renamed
or migrated wholesale.
