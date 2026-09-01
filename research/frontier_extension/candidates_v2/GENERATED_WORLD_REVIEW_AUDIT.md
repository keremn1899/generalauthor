# Generated-world review audit — frontier extension

## Result

**PASS: 14/14 candidate worlds admitted mechanically.** No participant
workspace was created and no participant/model execution was run. These are
review candidates, not final frozen experimental cases.

This audit verifies: deterministic oracle construction, exact canonical-to-typed
SQL parity, canonical-to-graph parity, and treatment expressibility gates. It
does not claim that human review has accepted the engineering realism or
natural-language adequacy of the generated worlds.

## Frozen conditions

| Item | Value |
| --- | --- |
| Candidate generator/version | `frontier-extension-candidates-v1` |
| Candidate directory | `research/frontier_extension/candidates_v2` |
| Graph treatment fingerprint | `fgt_7899e5ed448eedb70605` |
| SQLite version admitted | `3.51.1` |
| Participants run | `false` |

## Preregistered dose-response families

| Family | Cases | Required depth | Oracle-relevant closure |
| --- | --- | --- | --- |
| Depth / closure | FX01 → FX02 → FX03 | 3 → 5 → 8 | 18 → 64 → 240 |
| Intermediate reuse | FX14 → FX06 → FX07 | 3 → 5 → 8 | 20 → 92 → 300 |
| Cyclic topology | FX08 → FX09 | 5 → 8 | 82 → 250 |
| Negative / absence | FX10 → FX11 | 5 → 8 | 102 → 280 |

Mechanism probes, reported separately after execution: FX04 constrained
reachability; FX05 ordered relation sequence; FX12 qualified branching/set
composition; FX13 constrained multi-output topology.

## Mechanical-admission summary

| Case | Platform | Depth | Closure | Cycle | Absence | Named outputs | Answer IDs | Oracle | SQL parity | Graph parity | Feasible |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |
| FX01 | dependency_migration | 3 | 18 | False | False | 1 | 6 | True | True | True | True |
| FX02 | dependency_migration | 5 | 64 | False | False | 1 | 5 | True | True | True | True |
| FX03 | dependency_migration | 8 | 240 | False | False | 1 | 6 | True | True | True | True |
| FX04 | release_safety | 5 | 72 | False | False | 1 | 3 | True | True | True | True |
| FX05 | release_safety | 8 | 200 | False | False | 2 | 7 | True | True | True | True |
| FX06 | operational_containment | 5 | 92 | False | False | 4 | 10 | True | True | True | True |
| FX07 | operational_containment | 8 | 300 | False | False | 4 | 12 | True | True | True | True |
| FX08 | operational_containment | 5 | 82 | True | False | 2 | 7 | True | True | True | True |
| FX09 | operational_containment | 8 | 250 | True | False | 3 | 9 | True | True | True | True |
| FX10 | dependency_migration | 5 | 102 | False | True | 1 | 0 | True | True | True | True |
| FX11 | dependency_migration | 8 | 280 | False | True | 2 | 0 | True | True | True | True |
| FX12 | release_safety | 6 | 150 | False | False | 2 | 4 | True | True | True | True |
| FX13 | release_safety | 7 | 220 | False | False | 4 | 16 | True | True | True | True |
| FX14 | operational_containment | 3 | 20 | False | False | 3 | 10 | True | True | True | True |

Every graph candidate satisfied all frozen hard limits: depth ≤64,
oracle-relevant closure ≤3000, an estimated bounded program ≤12 steps, required
kinds/predicates present in the automatic minimal contract, representable named
outputs, ordered-sequence grammar, and set composition. SQLite recursive CTE
support was verified for each candidate; joins, subqueries, set operations,
temporary participant-authored materialization, aggregation, and projection
remain ordinary permitted SQL capabilities. No candidate contains a benchmark
authored query, traversal, closure, or path helper.

## Candidate integrity hashes

| Case | Canonical facts | Oracle | Typed SQLite projection | Graph projection |
| --- | --- | --- | --- | --- |
| FX01 | `926130a7bf7ddd69c92c7e3158d2cdf6f30f166a9868c72fa5c24b43b856437c` | `d9c8b1b9ebe8af24f96803c19bead4ae71d9edfcd1fb2b03d6dbf20b5cf6d4f8` | `066e4c5108ad73aba98151a3cd6fcc38bd63e6d6a211b9d62e79e9c8e4f5d699` | `059ae67003edc58df85ac515393acfeb5ad297607528733194a438ba6a728f5a` |
| FX02 | `412ba3df87bf4e1d3a3ffd35036a8c1bcadbe450b2e990ff1f029e3ccd2148eb` | `21a0424d5aeb305ff8d0d76f480af9555620aaed8b3187cce00d1d6100b8aa7c` | `1591dca06c8e4781ba7ce202b365292c50f1144e1c18767b0e07783aaa4ee7e2` | `5f3a3b0c1551b4e436fb27dc633f183781fa922821fa8151e0051cbeb3c668f7` |
| FX03 | `c0e714ac4bc8d0682f82a4b405aaa7f33925627fe04f198b7d6d63722749d01d` | `c1b076bcaa08a4a137c0476778fecfa0d9e42dbfd5d87147b19269df246332ec` | `6216b03b5eb0d0ad97e335b78323cc6133ece0cf09282d419037fdc49cfa4d2e` | `6f1c281a6d56c820192535643a3b1d3a933595e64c0fabdbc0f30a0a414f25ea` |
| FX04 | `4ca6940d68b704fe7ab938181a6ebd44959abcbc0231d21c5e8f1e6c4d0e0f24` | `f98e3f7f5bef3e5f84e24649a6f1e8e5285fafc5e18d5ba4144e3e3aef962b94` | `635ab36c93c498b3a4131ff81d1f5c426e8fd603794c7c60bc9ce61f10dc8c67` | `97973bf2ba88f98945def147e1bcf81f966eeab7897d98a6a8f436882af4872c` |
| FX05 | `094c040a56b06fec4fdc64b4074bf350e7de75f6ed07f6aa676a6a6993b00e9c` | `95f2f15421f7322f47db05491315a1b1c3a4616f08aed59f5766dddc91778253` | `ccb0799dac766c0ce365831556dbf514d95817484d6da309ca769f9f88fe6101` | `6191aba782f7a06030dc19ab41d5eeb96488bc3abd7e80c4947b2230764caf61` |
| FX06 | `4d2b1ef0de510bf38eff147729485677b70020b1354e8a2f5096e5f3cfe369ba` | `afbcb860948f6905400fb0b1f47c0c8acb71217f3d630191a1ac08937d631bdd` | `856efbf869ccad4169b9ddfaf0a017e1ad343832774208def08137a46aba064b` | `122955a80dc9797be54fe333cf7dbcff8aa3767cb18f496169fb05c2e91e116a` |
| FX07 | `d94050142df38165c73a1d50229f3b6525ac9d0f9b440394376ba4d221362782` | `ae9e7f1206e3b14aa66b7c42c381347a5cfa736cf5ffdd2bd96981d798b31234` | `9fd2b1dd2fcdc6b2300e7f6b2634cb60d1dcf5cc144f9db8eb3e3b7e20621b17` | `2948b08815cd166de881f6bfc5aa7d0c5b14ae45a81befa087132faa931b8ce1` |
| FX08 | `0c1c7ccdfc27bd13f9c00373b56bb7f55c3b787b23ec483105485cc9562f2f1b` | `840a92ab94a6597a9dfa3f15a20c7eda0036419b3fb895225afaee5fd5887bb6` | `1305e09b96aa0ff44958d3316874f709b1689d95fb9deef5b5fa86e5313a362c` | `6aa6a0e082727b84405c5d32fefe514b2c7d91852dcfd1f44d9b6687801d83cc` |
| FX09 | `d239910d4ef51dba7d58539849db0ed823652287f5e9c3ad8cc02e2112650e13` | `8ae17a03adba1e8f6500939e42966ce40bde56169c972c216c86b6a192e08118` | `46463e97f09f7904e72a48c9bb3e60bf85c1b2b86c7cecfd58f0c294aad61895` | `1e8453952e54f1e88fe38df77222224e84092fb3946d6884666588f637446581` |
| FX10 | `18894dde7ff0f9018f1cafa61083d090891376c57ef42bce2ed75148b519dcef` | `ebe9570467d6a4a2bfda64f26be1fbe30a75f790402d75a51361e624e15088c7` | `156a7fac5a50ea68f8fd8514bebec2017301fabc9ced582cb2e521be4a314594` | `df4fb229c5a6db3e8ba7505e7f5fb11cb4a1c91cd3c219db45d427ba10637f32` |
| FX11 | `3daf551b6796eb5cfc4fbdc734637220f27fd98ace6d7fa23b373c9eb9f4407c` | `c182a9164eecea5473c1b83c85c295970c52e5f8ad225e24a28a9eeef4671e4e` | `693570317b142af2cd4bb8649ca31928af98ec72e413fda6159bd64cf16a6084` | `4416f6b2a0c73ae1d3a1172b72f3351262028dcdd629e9cb5819859a8bfd0d1d` |
| FX12 | `b84105ea7031ff1128f9a134707c7473f9447a2728e538c3ee2d43af5c782606` | `c21637d79cfdf12672e9ad8e24964134c2726984c8b446e1300890f80373fb3a` | `10b48cce2202dc12f290929883c3668a7951c85eae9a4600ee35eca436eac23d` | `607ae071a4cdedd488371191b947fa448e0524e845cada0c34fa42240452242a` |
| FX13 | `752b6d208f5baa18722a27f89573cd6014ae7e44d2d343b81f7f05bc2ab4bae3` | `3ce260eb5ee592af8739d87914b04d10038577bea09f34c582ca1bbd0f4e7b7d` | `35631623074ec25e9dfaf30eca083f4a19ddc374a5cd82f497c79445e960500d` | `c874bb3c3e3ebbcf806edfd7a5646d7894d2d05b904ead88dd6360613b1d8308` |
| FX14 | `bc596a15aded3cabe9842f90d7aa280a3755d9ef37a60eabfbdc9fe2344bdeb4` | `6e4ee89d0f18e9564568ad15461063068285e6a3d6392abfb46c30154329cfdb` | `a670d5b8ed9d8e8ee16713631850496c1c3f3df418adba2d7b6b133d97ab7105` | `f62d020d934602743929c6e2ba113c4ca404ae5645555e5b49e84c47e2e1419d` |

## Prompt and neutral-oracle review inputs

### FX01 — Short consumer impact

For the Short consumer impact cutover, which production services remain affected? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 3, "op": "bounded_closure", "outputs": ["affected_services"], "predicate": "depends_on", "seed": "package:fx01-legacy"}`.

### FX02 — Medium consumer impact

For the Medium consumer impact cutover, which production services remain affected? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 5, "op": "bounded_closure", "outputs": ["affected_services"], "predicate": "depends_on", "seed": "package:fx02-legacy"}`.

### FX03 — Deep consumer impact

For the Deep consumer impact cutover, which production services remain affected? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 8, "op": "bounded_closure", "outputs": ["affected_services"], "predicate": "depends_on", "seed": "package:fx03-legacy"}`.

### FX04 — Approved migration route

Which production services require review because their approved migration route is approved end-to-end and avoids the deprecated integration boundary? Return stable IDs only.

Neutral oracle: `{"allowed_predicates": ["depends_on", "implements", "deployed_to"], "cycle_policy": "visited_nodes", "direction": "incoming", "forbidden_predicates": ["crosses_deprecated"], "max_depth": 5, "op": "constrained_reachability", "outputs": ["approved_route_services"], "predicate": "depends_on", "seed": "package:fx04-legacy"}`.

### FX05 — Ordered cutover chain

Which deployments are eligible for the ordered cutover chain only when its service-to-module-to-package-to-migration chain is complete? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 8, "op": "ordered_sequence", "outputs": ["eligible_services", "eligible_deployments"], "predicate": "depends_on", "predicates": ["implements", "depends_on", "affects", "targets"], "seed": "package:fx05-legacy"}`.

### FX06 — Medium release-readiness bundle

For the Medium release-readiness bundle cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 5, "op": "bounded_closure", "outputs": ["affected_services", "affected_deployments", "uncovered_services", "boundary_crossings"], "predicate": "depends_on", "seed": "package:fx06-legacy"}`.

### FX07 — Large release-readiness bundle

For the Large release-readiness bundle cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 8, "op": "bounded_closure", "outputs": ["affected_services", "affected_deployments", "uncovered_services", "boundary_crossings"], "predicate": "depends_on", "seed": "package:fx07-legacy"}`.

### FX08 — Cyclic service containment

For the Cyclic service containment cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 5, "op": "bounded_closure", "outputs": ["affected_services", "owners"], "predicate": "depends_on", "seed": "package:fx08-legacy"}`.

### FX09 — Deep cyclic migration containment

For the Deep cyclic migration containment cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 8, "op": "bounded_closure", "outputs": ["affected_services", "owners", "affected_deployments"], "predicate": "depends_on", "seed": "package:fx09-legacy"}`.

### FX10 — Medium legacy-clearance proof

For the Medium legacy-clearance proof cutover, which production services remain affected? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 5, "op": "bounded_closure", "outputs": ["affected_services"], "predicate": "depends_on", "seed": "package:fx10-legacy"}`.

### FX11 — Large legacy-clearance proof

For the Large legacy-clearance proof cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 8, "op": "bounded_closure", "outputs": ["affected_services", "affected_deployments"], "predicate": "depends_on", "seed": "package:fx11-legacy"}`.

### FX12 — Boundary-qualified impact

Which affected production services both cross a regulated boundary and lack integration verification? Return stable IDs only.

Neutral oracle: `{"cycle_policy": "visited_nodes", "difference": ["qualified", "verified"], "direction": "incoming", "intersection": ["affected", "boundary_sensitive"], "max_depth": 6, "op": "qualified_set_composition", "outputs": ["boundary_unverified_services", "affected_deployments"], "predicate": "depends_on", "seed": "package:fx12-legacy"}`.

### FX13 — Multi-output constrained rollout

For the multi-output constrained rollout, return affected services, eligible deployments, uncovered integration tests, and regulated-boundary crossings as stable IDs.

Neutral oracle: `{"allowed_predicates": ["depends_on", "implements", "deployed_to", "crosses"], "cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 7, "op": "constrained_reachability", "outputs": ["affected_services", "eligible_deployments", "uncovered_services", "regulated_services"], "predicate": "depends_on", "seed": "package:fx13-legacy"}`.

### FX14 — Small closure-reuse control

For the Small closure-reuse control cutover, return the required production impact and safety information as stable IDs.

Neutral oracle: `{"cycle_policy": "visited_nodes", "direction": "incoming", "max_depth": 3, "op": "bounded_closure", "outputs": ["affected_services", "affected_deployments", "uncovered_services"], "predicate": "depends_on", "seed": "package:fx14-legacy"}`.


## Required human decision before participant execution

Approve or reject these candidate worlds as a batch after reviewing their
prompts, canonical facts, and oracle artifacts. On approval, freeze the
candidate hashes, adapter hash, product commit, Python environment, and case/
arm ordering in a campaign manifest. Do not replace individual cases after any
participant outcome.
