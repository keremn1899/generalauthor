# Open weaknesses

**Status:** working note after the NPDES residual-semantics campaign and End-to-End Programmability Probe v0.  
**Not:** a kernel change, Constructor promotion, fifth-domain plan, or product spec.

These are the current iffy bits. Evidence is what the sealed probes actually showed. “What would improve confidence” is the next experimental move, not a commitment to implement it.

Authorities this note sits with:

- [`ARCHITECTURE.md`](../ARCHITECTURE.md) — layers; kernel moves only on a concrete counterexample
- [`minimal_semantic_integration_synthesis_v0.md`](minimal_semantic_integration_synthesis_v0.md) — what the NPDES campaign appears to have established
- [`drop_in_harness_v0_spec.md`](drop_in_harness_v0_spec.md) — guest harness; still unimplemented

Sealed results this table draws on (do not modify):

| Probe | Path | Label |
| --- | --- | --- |
| Purpose-First Python Spine | `domains/npdes/purpose_first_python_spine_v1/reports/purpose_first_python_spine_v1.md` | `PURPOSE_FIRST_PYTHON_SPINE_SUPPORTED` |
| Semantic Spine Anatomy | `domains/npdes/semantic_spine_anatomy_v1/reports/semantic_spine_anatomy_v1.md` | see anatomy reports |
| Obligation-Driven Targeted Resolution | `domains/npdes/obligation_targeted_resolution_v1/reports/obligation_targeted_resolution_v1.md` | `MIXED_OBLIGATION_RESOLUTION_RESULT` |
| End-to-End Programmability v0 | `domains/npdes/end_to_end_programmability_v0/reports/end_to_end_programmability_v0.md` | `END_TO_END_PROGRAMMABILITY_SUPPORTED` |
| Drop-in Harness v0 spec | `reports/drop_in_harness_v0_spec.md` | `DROP_IN_HARNESS_SHAPE_COHERENT` (design only) |

---

## Table

| Area | Current concern | Evidence level | What would improve confidence | Where this showed up |
| --- | --- | --- | --- | --- |
| Semantic-delta materialization | A supported proposal can select 0 rows, crash, or leave parent/child admission inconsistent | Observed weakness | Deterministic replay of frozen proposals with exact expected deltas | Obligation T1 pass/fail completed with **0** `binary_pass_fail_*` rows (`LIMIT_VALUE_STANDARD_UNITS=='9A'`). T2 pass/fail disposable apply **crashed**. T2 geometric-mean: parent `UNRESOLVED`, TDS child `ADMIT_DISPOSABLE`. E2E State C had to use **T3** (8 `pass_fail_outcome_reporting` rows) rather than T1, and skipped State D rather than repair the mismatch. |
| Obligation factorization grain | Initial grouping often needs refinement after evidence contact | Mixed | See whether the same behavior recurs in a new domain and still stays compact | Obligation probe: 8 selected → refinements on 12/24 Arm B cells; final grain ~12–16 questions, not thousands of rows. Not occurrence-level explosion; not compact enough for the strict success label. Anatomy: T3 vs T5 group-count variance is grain, not coverage. |
| Establishability / stopping | Research evaluator knew whether evidence existed; a product host will not have that oracle | Important unknown | Host must decide “keep looking vs corpus insufficient” without hidden GOLD | Obligation `evaluator_only/establishability.json` was hidden from the host. NODI C/9 correctly stayed `EVIDENCE_INSUFFICIENT` because no codebook is in the frozen packages. That distinction used a post-hoc audit the product cannot ship. |
| Corpus-level authority questions | `document_authority` needed much broader reading than ordinary obligations | Observed weak spot | New domain with explicit competing authoritative documents | Obligation `document_authority` opened most of the 12 permit-text files; T1 recorded a budget exception. Targeted retrieval otherwise stayed obligation-local. |
| Occurrence fact vs reusable meaning | Local facts can support one occurrence without establishing a code meaning globally | Observed subtlety | New domain with repeated codes/rules plus context-specific exceptions | Obligation Arm A NODI 9: A04/A05 `UNRESOLVED` vs A06 `SUPPORTED_NEGATIVE` on a WET-retest row (optional-retest facts, not a code legend). Arm B correctly refused a NODI-9 World legend. E2E kept 150 C + 36 9 as `nodi_code_semantics` unresolved. |
| Epistemic read surface | A fresh agent over-read hole prose as if missing semantics were established | Observed minor weakness | Make unresolvedness unmistakable through ordinary relational/read conventions | E2E State A Q3: `PARTIAL_FROM_WORLD` — treated T5 `conditional_discharge_dependent_monitoring` hole prose as already-established condition meaning. Compiled `monitoring_condition` did not exist until State B. State C Q3 was `CORRECT_FROM_WORLD`. Compact header READ RULES did not fully block the over-read. |
| Spine factoring / minimality | Agents find the distinctions well but express them at inconsistent granularity | Mixed | New-domain convergence + post-construction factoring | Anatomy: E1 7/7 stable core; factorized schemas ~11–16; T3=31 vs T5=8 hole groups from grain (seasonal months, comment families), not different primary coverage. Much minimality is safely post-construction. |
| Semantic frontier recall | Earlier NPDES constructors missed staged TDS and source authority | Observed capability weakness | New-domain purpose where those semantics are central rather than peripheral | Purpose-First Python Spine recovered WHEN DISCHARGING / staged TDS / source authority 5/5 after the spine-compiler and prose probes had missed them as purpose-reachable holes. That is a capability win on a known miss, not evidence those families are now reliably found in a new domain. |
| Cross-reconstruction app stability | Different constructors may name equivalent semantics differently | Known pressure, untested product failure | Defer until persistent/generated apps actually break | E2E held one T5 contract fixed while facts were enriched; consumer rewrite count = 0. That is **not** the ABI question. E2E Q22 and the drop-in spec both defer `semantic_identity` / cross-reconstruction until a real consumer breaks. |
| Kernel adequacy | No demonstrated missing representational primitive | Strong so far | Don't touch unless a new domain produces a concrete counterexample | Matches [`ARCHITECTURE.md`](../ARCHITECTURE.md) §1. E2E: no correctness failure that required a new kernel primitive, graph API, or Source IR. TaskView/kernel were not modified. |

---

## How to read the evidence levels

- **Observed weakness** — the sealed run actually did this. Do not round it up into a new subsystem.
- **Observed subtlety / minor weakness** — real, but the honest behavior (leave unresolved; keep occurrence ≠ legend) also showed up.
- **Mixed** — the mechanism works at reusable grain and still needs a second domain before promotion.
- **Important unknown** — the research protocol used evaluator knowledge the product host will not have.
- **Known pressure, untested product failure** — do not implement ABI because it would be convenient.
- **Strong so far** — absence of a counterexample, not a proof the kernel is finished.

---

## What this note does not do

It does not promote obligation factoring, REFINED, evidence plans, or a semantic-family taxonomy into the kernel.

It does not start a fifth domain by itself. Several rows say a new domain would raise confidence; that is a test design, not a schedule.

It does not reopen TaskView because consumers found hole prose easy to over-read. That is a read-surface / WORLD-vs-PURPOSE convention problem until a domain cannot represent a required distinction.

---

## STOP

Record only. No Constructor change. No TaskView/kernel change. No harness implementation. No ABI. No fifth domain.
