# Oracle-free operational frontier (BOM S1)

Frozen before C0 evaluation. Provider/model inference calls: **0**.

## Frozen operational frontier

- Purpose: `viable_replacement` revision 1
- Statement: Determine viable replacement options for the represented BOM replacement cases.
- Generation rule: `viable-replacement-candidate-context-v1`
- C1 world revision: 164
- Mechanically compiled `candidate_replacement` pairs: 2
- Purpose-required candidate/context cases: 3
- Semantic obligations: 3
- Fingerprint: `sha256:c012b4db5d9f8b02dd396a774cfd2fbde2442e34cc765aad9827f827d5f142c9`

### Rule

Each mechanically compiled candidate_replacement(new_part, old_part) together with each deployment_environment of a BOM item whose required part_type matches both parts demands acceptable_replacement(new_part, old_part, context) before a viable-replacement answer is established.

### Obligations

- `acceptable_replacement(part:R210, part:R200, context:high_vibration_cabinet)` demanded by purpose `viable_replacement` revision 1
- `acceptable_replacement(part:X110, part:X160, context:indoor_panel)` demanded by purpose `viable_replacement` revision 1
- `acceptable_replacement(part:X110, part:X160, context:outdoor_enclosure)` demanded by purpose `viable_replacement` revision 1

## Oracle residual (loaded only after freeze)

`F_oracle = C0 − C1`

- `acceptable_replacement(part:R210, part:R200, context:high_vibration_cabinet)`
- `acceptable_replacement(part:X110, part:X160, context:outdoor_enclosure)`

## Comparison

| metric | value |
| --- | --- |
| true positives | 2 |
| false positives | 1 |
| false negatives | 0 |
| precision | 2/3 (0.6666666666666666) |
| recall | 2/2 (1.0) |
| exact frontier match | False |

True positives:

- `part:R210, part:R200, context:high_vibration_cabinet`
- `part:X110, part:X160, context:outdoor_enclosure`

False positives:

- `part:X110, part:X160, context:indoor_panel`

False negatives:

(none)

## Required interpretation

### 1. Can the semantic frontier be generated without C0?

Yes. The generator receives only a compiled C1 TaskView and the frozen purpose
contract. Candidate identities come from World IR joins. C0 is not an input.

### 2. What exactly created each obligation?

Each obligation is a demanded `acceptable_replacement(new, old, context)` for a
mechanically compiled `candidate_replacement` pair together with each
`deployment_environment` of a BOM item whose required `part_type` matches both
parts, when that exact tuple is not already established in SemanticWorld.

### 3. Is each obligation tied to a declared computation/purpose rather than generic missing world knowledge?

Yes. Obligations are not "all semantic facts missing from World IR". They are
viability judgments required by purpose `viable_replacement` for concrete
mechanically generated replacement cases. Unrelated missing facts do not appear.

### 4. Does resolving an obligation remove it mechanically?

Yes. Inserting the demanded tuple into a temporary copy of C1 removes that
obligation on regeneration. Remaining unresolved demand is unchanged.

### 5. Do new relevant candidates create new obligations?

Yes. Adding one extra `candidate_replacement` that falls under the purpose and
lacks an `acceptable_replacement` judgment adds exactly one obligation.

### 6. Does irrelevant world growth leave it unchanged?

Yes. Additional part, listing, and BOM records that do not create a new
purpose-required candidate/context case leave the operational frontier unchanged.

### 7. Does the operational frontier exactly match the historical oracle residual for frozen S1?

No. Precision is 2/3; recall is 1.0. The operational rule uses every mechanically represented BOM context of the matching part type. The hidden C0 residual encodes a narrower engineering-note restriction that is not present as compiled World IR. The extra operational demand is a false positive relative to C0, not a generator read of C0.

### 8. What remaining role did C0 play?

Evaluation oracle only. It was loaded after `operational_frontier.json` was
serialized, to compute `F_oracle = C0 − C1` and score the frozen obligations.
C0 was not a constructor input.

## Counterfactual checks

Recorded by `tests/semantic_integration/test_operational_frontier.py`:

1. Already-resolved: inserting one required `acceptable_replacement` into a C1 copy removes that obligation.
2. Additional candidate: one extra purpose-covered `candidate_replacement` adds one obligation. It is not added to C0 and is not scored against the frozen oracle.
3. Irrelevant growth: unrelated BOM/part/listing records leave the frontier unchanged.

## LLM semantic authoring (not implemented in this run)

These surfaces are identified only. This experiment did not invoke a model.

### ASSERTION AUTHORING

Grounded tuples from bounded evidence.

Already empirically exercised: the authorized BOM C2 campaign inserted two
packet-grounded `acceptable_replacement` ACCEPT judgments. This run does not
repeat that.

### VOCABULARY AUTHORING

Candidate relation names, roles, and meanings demanded by unresolved distinctions.

Hypothesis only. Not implemented or tested here.

### DERIVATION AUTHORING

Candidate deterministic rules over existing relations.

Hypothesis only. C1's SQL derivations were human-authored earlier; this run
does not ask a model to propose rules.

### ABSTRACTION AUTHORING

Candidate reusable semantic concepts over lower-level evidence.

Hypothesis only. Not implemented or tested here.

Currently only bounded assertion authoring has been exercised directly.
