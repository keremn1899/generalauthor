# Semantic Spine Anatomy & Minimality Probe v1

Sealed interpretation: **STABLE_CORE_OVERFACTORED**

Not constructor repair. Original `construction.py` programs, Worlds, holes, Constructor v3.1.1, TaskView/kernel, P3/P5, Spine Compiler Probe v1, and prose probes were not modified.

## MEASURED headline

| trial | semantic LOC | nonblank LOC | % semantic-painted |
| --- | --- | --- | --- |
| T1 | 392 | 657 | 60 |
| T2 | 482 | 957 | 50 |
| T3 | 492 | 762 | 65 |
| T4 | 339 | 619 | 55 |
| T5 | 359 | 609 | 59 |

Mean factorized requirement schemas: 14.0. Mean candidate obligations: 35. Mean hole occurrences: 2972.

Baseline reruns of unmodified copies: see ablation_results.md.

## Required answers

### 1

Physical LOC is 652–1,015 (T5–T2). Semantic-painted nonblank LOC is 339–492 (50–65% of nonblank). That paint is mostly relation-signature and require_* blocks, not hundreds of distinct concepts. Factorized requirement schemas are 11–16 per trial. Mechanical+OTHER (grounding loops, helpers, comments) is the rest of the file.

### 2

Per trial: referent kinds 4–11 (T3 has 39 referent() calls over fewer kinds); relations 8–25; unique require names 19–30; factorized requirement schemas 11–16; spine requirement rows 48–1,273.

### 3

5/5: interpret_comment, interpret_frequency, interpret_nodi, interpret_optional_monitoring, interpret_qualifier, unique_applicable_limit, CandidateCorrespondence, DocumentInventory, Fy2025Scope, LimitBase, MeasurementBase, NumericComparison

### 4

Trial-local (1/5 or 2/5): aggregated_reporting, sample_type, value_type, unit, statistical_base, report_only named gap, SeasonalMonth relations, CodePayload, T1 catalog-variant cardinality hole. Frequency interpretation is 5/5 but locally redundant for primary E1.

### 5

All five authored interval-aware correspondence, comment opacity, NODI opacity, a numeric/non-numeric split, uniqueness, and document inventory. Frozen E1 is triggerability (any allowed failure kind + seam tokens). It did not require identical holes.

### 6

T3=31 vs T5=8 is factorization and grain: T3's 12 seasonal month names alone are 12 groups; ablating that loop drops T3 to 19 groups with E1 still 7/7. T5 emits 8 groups from a tight schema set plus three comment-literal unresolved families. Not different primary coverage.

### 7

A pure code duplication: 0 emitted rows. B instance expansion and C missing parameterization dominate (T3 C=1,239 rows from per-row unresolved). T3 E=12 is twelve seasonal surface names, not twelve ontologies. D false duplication was not needed.

### 8

Mean candidate obligations ≈ 35 after grouping hole (requirement, observed value/kind).

### 9

Mean occurrences 2972 versus mean ~14 factorized schemas and ~35 obligations.

### 10

PURPOSE_REACHABLE: CandidateCorrespondence, uniqueness, NODI, comments/WHEN, numeric comparison, document inventory/text hole, FY2025 scope. NOT_PURPOSE_REACHABLE relative to primary E1: seasonal months, sample type, unit/value-type, frequency (stable but ablation-redundant), T5 pass-fail/geometric extras. AMBIGUOUS: optional-monitoring and limit-type (on the path, not single-element proven).

### 11

REQUIRED_FOR_PURPOSE (7): T1 unique_catalog (cardinality hole), T1 nodi, T2/T4/T5 unique (authored uniqueness disappears), T5 nodi, T5 document-text unresolved. 23 locally redundant including T3's 12-month loop, freq/sample-type/unit/value-type, T5 aggregated/pass-fail, and pairwise WHEN substitutes.

### 12

Yes, locally: frozen E1 never moved; many extras drop without precise-coverage loss; T5 is already near a deletion-minimal draft. Not a global ontology minimum. T1 uniqueness is a pair (catalog hole + satisfied schedule unique).

### 13

Main complexity is requirement instantiation (C loops, 48–1,273 rows) plus physical grounding (date/join maps), then execution scaffolding. Conceptual modeling of the core is small (~6 stable requirement schemas + ~6 stable relation schemas).

### 14

Three supported motifs: uniqueness after seeing temporal/catalog multiplicity; refuse opaque NODI/comment codes as World truth; inventory documents and leave narrative unresolved.

### 15

T1/T5 are architecturally safe fixture-sensitive hole detectors (literal match → unresolved, no World assertion). They do not undermine the result. T2–T4 show the reusable nonempty-comment pattern.

### 16

About six core certification questions (interval geometry, uniqueness cardinality, NODI, comments/WHEN DISCHARGING, report-only vs numeric, document text) plus a short extras list. Not raw Python and not 2,972 occurrences.

### 17

Yes. First-shot construction produced a draft semantic spine: 5/5 E1=1.00 from a stable core, with overfactored extras a human can factor or delete. Conversational refinement is the natural next probe, not a fifth domain.

### 18

Much of the minimality is safely post-construction: 23/30 single-element drops were locally redundant; T3 seasonal loop is the clearest factoring win. First-shot authoring need not emit the minimal schema set, but should keep uniqueness, NODI, comments, and document-text holes.

## Interpretation

**STABLE_CORE_OVERFACTORED**

Complexity measures used descriptively: semantic elements, relation schemas, requirement schemas, grounded instances, dependency depth. No ontology-size scoring formula.

## STOP

No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5. No conversational certification. No fifth domain.
