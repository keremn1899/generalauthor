# Semantic Proposal & Scope Clarification Microprobe v1

Sealed interpretation: **PROPOSAL_CLARIFICATION_LOOP_SUPPORTED**

Not a product UI. Constructor v3.1.1, TaskView/kernel, P3/P5, Purpose-First Python Spine Probe, Semantic Spine Anatomy Probe, and Conversational Semantic Review Probe were not modified.

Utterances were injected exactly. This is evaluator/host-agent evidence, not real-user usability.

## Required answers

### 1

MEASURED: Case 1 disposition=NEEDS_CLARIFICATION; mutated_before_accept=False; committed=False.

### 2

# Clarification needed: what is wrong about "one governing limit per measurement"?

You said the draft is wrong to treat each FY2025 measurement as having exactly one governing applicable numeric limit. That rejection is clear, but it could point in very different directions—and those directions produce very different results on this fixture.

## Where the disagreement sits

The draft currently builds **824** measurement–limit pairs (one per FY2025 measurement) by following the limit identity already carried on each DMR row (`LIMIT_VALUE_ID` and `LIMIT_SET_SCHEDULE_ID`). It then treats the "exactly one applicable limit per measurement" rule as **satisfied** on this data.

A separate issue summary describes pairing differently—as if each measurement were matched against all permit limit rows by permit, outfall, parameter, and whether the monitoring period falls inside each limit's effective dates. Under that catalog-style rule, most measurements would match **multiple** permit limit rows (overlapping or staged intervals), not one.

So the open question is not whether you disagree with the draft's conclusion—you already said you do—but **which part** you are rejecting.

## What would

### 3

MEASURED: Case 2 disposition=NEEDS_CLARIFICATION; n_dry_runs=2; underclarified=False.

### 4

MEASURED: Case 3 overclarified=False disposition=NEEDS_CLARIFICATION; Case 4 overclarified=False; Case 6 overclarified=False; Case 7 overclarified=False.

### 5

MEASURED: Case 3 inferred scope=ONE_PURPOSE intended=ONE_PURPOSE silently_world=False.

### 6

MEASURED: Case 4 scope=ONE_PURPOSE intended=ONE_PURPOSE silently_world=False.

### 7

MEASURED: Case 5 scope=WORLD intended=WORLD; damage={'unexpected_relation_count_changes': [], 'unexpected_requirements': [], 'damaged': False}.

### 8

MEASURED: Case 6 epistemic=USER_UNCERTAINTY intended=USER_UNCERTAINTY; committed=False.

### 9

MEASURED: Case 7 epistemic=USER_CERTIFIED_POLICY vs Case 8 epistemic=USER_ASSERTED_EXTERNAL_FACT.

### 10

MEASURED: Case 8 epistemic=USER_ASSERTED_EXTERNAL_FACT intended=USER_ASSERTED_EXTERNAL_FACT; semantic_delta=Add a document_kind_precedence relation recording that final_permit legally takes precedence over fact_sheet when narrative permit conditions conflict. Keep permit_document_text_not_available unresolved because structured sources still lack document body text. Split the former document_authority uncertainty by adding a narrower unresolved item for precedence among other inventoried document kinds (statement_of_basis, reasonable_potential, minor_modification, appendices, etc.)..

### 11

OBSERVED from proposal utterance_understood fields vs frozen utterances; see proposals.md.

### 12

MEASURED consequence overlap: case4_purpose_scope faithful=True overlap=[12, 105, 186, 342, 535, 824]; case5_world_generalization faithful=True overlap=[12, 105, 186, 342, 535, 824]; case6_uncertainty faithful=True overlap=[186]; case7_policy faithful=True overlap=[12, 105, 186, 536]; case8_external_fact faithful=True overlap=[12, 105, 186, 342, 536, 824]

### 13

MEASURED commit_matches_proposal: case4_purpose_scope=True; case5_world_generalization=True; case7_policy=True; case8_external_fact=True

### 14

MEASURED: 3 clarification dispositions out of 8 cases.

### 15

MEASURED host consequence_divergence flags: case1_bare_rejection=True; case2_underspecified=True; case3_substantive=True; case4_purpose_scope=False; case5_world_generalization=False; case6_uncertainty=False; case7_policy=False; case8_external_fact=False

### 16

MEASURED unrelated damage on commits: case4_purpose_scope={'unexpected_relation_count_changes': [], 'unexpected_requirements': [], 'damaged': False}; case5_world_generalization={'unexpected_relation_count_changes': [], 'unexpected_requirements': [], 'damaged': False}; case7_policy={'unexpected_relation_count_changes': ['document_conflict_authority'], 'unexpected_requirements': [], 'damaged': True}; case8_external_fact={'unexpected_relation_count_changes': ['document_kind_precedence'], 'unexpected_requirements': [], 'damaged': True}

### 17

Interpretation label: PROPOSAL_CLARIFICATION_LOOP_SUPPORTED. The proposal → dry-run → clarify/accept loop held. Ambiguous uniqueness utterances (Cases 1–2) did not mutate durable state. Case 3 still asked a consequence-driven follow-up after the meaning was largely specified. Case 8 labeled an unverified legal claim USER_ASSERTED_EXTERNAL_FACT but still committed a WORLD-mode precedence row. That combination supports the loop as a research safety boundary, not yet as a product architecture.

## OBSERVED (evaluator, not usability)

All successful host calls reported Composer 2.5. No durable construction.py mutation before ACCEPT. Cases 1 and 2 localized pairing-rule vs uniqueness-cardinality disagreement with dry-run splits (824 vs 4,076 pairs in Case 1; same split in Case 2) and asked ordinary-language questions without a closed A/B/C menu.

Case 3 inferred ONE_PURPOSE (not WORLD) from a scope-implicit correction, then still classified NEEDS_CLARIFICATION because “genuinely different limit types” forked 535 vs 1,919 unresolved items after the same 824→2,812 pair expansion. That is consequence divergence under the probe rule, against the case’s preferred READY_FOR_ACCEPTANCE.

Case 4 narrowed to Purpose A, committed AT_LEAST_ONE uniqueness, pairs 824→2,812, comparisons 342→1,336, WORLD relation modes unchanged, unrelated hole groups unchanged, revert restored baseline and sources.

Case 5 promoted measurement_limit_pair PURPOSE→WORLD for the same pair expansion without adding Purpose B/C requirements. Uniqueness requirement purpose remained [A] while the derived relation became WORLD.

Case 6 kept NODI 9 UNINTERPRETED (USER_UNCERTAINTY, ONE_SOURCE_VALUE) and did not rewrite construction; it also did not add an extra explicit unresolved family for code 9.

Case 7 encoded analysis policy as PURPOSE-mode document_conflict_authority grounded in the utterance (USER_CERTIFIED_POLICY), leaving narrative text unresolved.

Case 8 distinguished the utterance as USER_ASSERTED_EXTERNAL_FACT and grounded the row as `basis=user_asserted_external_fact` rather than a CSV source, but still mapped a WORLD-mode document_kind_precedence fact. Two encodings (WORLD legal vs PURPOSE policy) had identical counts, so it did not clarify.

## HYPOTHESIS

Host-owned formalization plus dry-run consequence inspection can sit behind unrestricted natural language if durable commit waits on acceptance. Remaining risks are over-clarifying identity forks inside an otherwise clear correction, and committing unverified external-legal assertions into WORLD relations.

## Interpretation

**PROPOSAL_CLARIFICATION_LOOP_SUPPORTED**

## STOP

No UI. No kernel or constructor modification. No conversational-editing promotion. No semantic-editing DSL. No prose retrieval. No P5. No fifth domain. No real-user usability claims.
