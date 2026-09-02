# World IR as a Python programming substrate (BOM S1)

No model/provider inference. Provider/model calls: **0**.

This freeze is the human-written benchmark later LLM RAW vs WORLD
programming experiments should reuse unchanged.

## Success criteria

1. Three useful analyses were written entirely over the compiled World.
2. WORLD computation is ordinary Python/SQL.
3. Source-specific reconciliation moved out of WORLD analysis programs.
4. World relations were reused across distinct analyses.
5. Epistemic status and provenance remained accessible.

## Conditions

- RAW starts from the frozen S1 fixture files.
- WORLD receives a newly constructed SemanticWorld copy (C1 compile + copied C2 ACCEPT tuples) and operational obligations. After construction it does not open source files.

## Correctness

- `analysis_a`: RAW matches WORLD = True; RAW files 3 (1943 bytes); WORLD files 0 (0 bytes).
- `analysis_b`: RAW matches WORLD = True; RAW files 3 (1943 bytes); WORLD files 0 (0 bytes).
- `analysis_c`: RAW matches WORLD = True; RAW files 3 (2595 bytes); WORLD files 0 (0 bytes).

## Epistemic safety

- Indoor-panel case: `part:X110` / `part:X160` / `context:indoor_panel`.
- `semantic_state` = `unresolved`; `epistemic` = `UNRESOLVED`.
- Absence from `acceptable_replacement` was not treated as false.
- `ADJUDICATED_FALSE` is not representable in the current assertion model (interface limitation).

## Provenance

- `inspect_tuple` on `acceptable_replacement` origin `SEMANTIC`.
- grounding `SOURCE` source `bom.csv` at `row 2 (bom_item=BOM-A)`.
- grounding `SOURCE` source `engineering_notes.md` at `lines 6-14 (ER-1)`.
- grounding `WORLD` source `None` at `None`.

## Programming burden (diagnostic LOC / AST, not value)

- RAW nonempty lines: 332 (preparation 103, analysis 229)
- WORLD nonempty lines: 274 (analysis 265, plus relation_rows helper)
- RAW source-schema fields referenced: ['availability', 'bom_item', 'deployment_environment', 'lifecycle', 'listings', 'manufacturer_part_number', 'max_temp_c', 'min_temp_c', 'observed_voltage_v', 'part_number', 'part_type', 'rated_voltage_v', 'required_voltage_v', 'sku', 'supplier']
- WORLD source-schema fields referenced: []
- WORLD relations referenced: ['acceptable_replacement', 'candidate_replacement', 'deployment_environment', 'eligible_part', 'lifecycle', 'listing_availability', 'listing_of', 'part_type', 'rated_voltage', 'requires_type', 'spec_conflict', 'temperature_compatible', 'voltage_compatible']

## Structural comparison

### analysis_a
RAW:
- parse manufacturer.csv and bom.csv
- parse engineering_notes.md Candidate records
- normalize part/bom/context identifiers
- join replacement candidates to BOM items by part_type
- reconstruct mechanical eligibility from voltage/temperature/lifecycle fields
- interpret note backticks as context-qualified acceptance
- classify remaining demanded cases as unresolved, not false
WORLD:
- query candidate_replacement, part_type, requires_type, deployment_environment
- query eligible_part and acceptable_replacement
- join demanded cases in SQL
- classify semantic state from asserted tuples vs obligation list

### analysis_b
RAW:
- reuse manufacturer/BOM/notes parsers
- recompute voltage, temperature, and lifecycle constraints per BOM item
- reconstruct acceptance from note context mentions
- separate preventing constraints from unresolved semantic acceptance
WORLD:
- query voltage_compatible, temperature_compatible, lifecycle, acceptable_replacement
- consult completeness receipts before treating a derived miss as failure
- treat missing acceptable_replacement plus an obligation as uncertain, not false

### analysis_c
RAW:
- parse manufacturer.csv and suppliers.json
- reconcile manufacturer_part_number to part_number
- detect multiple voltage observations per part
- join conflicted parts to BOM items by part_type
- recompute eligibility from manufacturer ratings
WORLD:
- query spec_conflict, rated_voltage, requires_type, eligible_part, listing_of
- inspect_tuple on rated_voltage to recover source handles

## World reuse

- A∩B: ['acceptable_replacement', 'candidate_replacement', 'deployment_environment', 'part_type', 'requires_type']
- A∩C: ['eligible_part', 'part_type', 'requires_type']

## Interface assessment

SQL + ordinary Python + small semantic introspection was sufficient.
No domain query language was added.

- Used: ['query_semantic', 'inspect_tuple', 'latest_completeness', 'is_stale', 'relation_tuples (via relation_rows helper)']
- Limitation: ADJUDICATED_FALSE is not representable: there is no negative semantic assertion form. Missing acceptable_replacement cannot be read as false.

## Conclusions

### MEASURED

- Three analyses ran in both conditions with identical canonical outputs.
- WORLD analysis opened 0 raw source files and consumed 0 raw source bytes after construction.
- Indoor-panel acceptable_replacement is UNRESOLVED, not false.
- inspect_tuple returned stored SOURCE groundings for an accepted semantic tuple.

### OBSERVED

- RAW programs parse CSV/JSON/Markdown, normalize identifiers, and reconstruct eligibility, context, and acceptance.
- WORLD programs query compiled relations and compute over those tables in ordinary SQL/Python.
- The same World relations are reused across distinct analyses.

### HYPOTHESIS

- An LLM writing RAW Python would spend tokens and tool calls on parsers, identifier joins, and note interpretation.
- An LLM writing WORLD Python would spend them on relation names, SQL joins, and epistemic status.
- This experiment does not measure that difference.

## Later LLM experiment

Reuse `raw/`, `world/`, `expected/`, and `expected/interfaces.json` unchanged.
Do not run that experiment here.

