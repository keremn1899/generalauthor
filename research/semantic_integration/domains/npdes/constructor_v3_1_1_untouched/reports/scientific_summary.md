# Scientific summary — untouched fourth domain (EPA NPDES)

Frozen Constructor v3.1.1. Five isolated Composer 2.5 trials. No constructor repair after this file.

Companion: `constructor_report.md`, `held_out_d.md`, `world_programming.md`, `evaluation.json`, `world_freeze.json`.

---

## Primary outcomes

### A. Kernel survival

**MEASURED.** New primitive required: **no**. Possible kernel counterexamples: **none**.

Closed-world “not required” is an implementation limitation handled as UNRESOLVED or as positive NODI evidence. Representable with existing kernel.

### B. Purpose-driven vocabulary

**MEASURED.** Useful NPDES vocabulary invented without a supplied ontology. 15–27 relations per trial. WORLD vs PURPOSE split is directionally correct. Names are not stable across trials.

### C. Mechanical compilation

**MEASURED.** Worlds are large and mostly compiled DMR/limit state plus derived candidates.

| Trial | Assertions | ASSERTED | DERIVED | Ungrounded |
|---|---|---|---|---|
| T1 | 6735 | 2003 | 4732 | 0 |
| T2 | 6595 | 1113 | 5482 | 0 |
| T3 | 8284 | 1060 | 7224 | 0 |
| T4 | 7037 | 3187 | 3850 | 0 |
| T5 | 4506 | 996 | 3510 | 0 |

T1 WORLD semantic BASE is tiny (6 permit-condition tuples; 0 no-discharge assertions). Mechanical compilation of structured ICIS rows is the bulk of World.

### D. Semantic frontier

**MEASURED.** Frontier shifted to applicable limits, monitoring obligations, and missing-evidence — not identity reconciliation. GOLD S recall 0.25–0.75. Persistent misses on all five trials: staged TDS (`S-FARM-TDS-STAGE`), source-authority (`S-SOURCE-AUTHORITY`).

### E. Semantic safety

**MEASURED.** Provenance: 0 ungrounded on all trials. P5 DISTINCT gate idle (wrong frontier type).

Unsupported closures:

- T2 Purpose A: 10 report-only rows as numeric exceedance.
- T3 Purpose A: 109 false exceedances / 131 compared.
- T1/T3 Purpose D: NODI 9 (not required) classified as missing-required follow-up (12 unique keys).

UNRESOLVED preservation: widespread and usually correct. NODI C was not converted into violations.

### F. Contract / compiler integrity

**MEASURED.** ABI `ok=False` on all five trials. `SATISFIED ⇒ nonempty bound table` violations: **0**. Ambiguity and `NOT_MATERIALIZABLE` reported. Purposes were **not** marked `INCOMPLETE_PURPOSE` because P8 is LLM `derive_purposes.py`, not the diligence fail-closed projector. Silent projection of incomplete ABIs occurred.

### G. Held-out reuse

**MEASURED.** D ran WORLD_ONLY, sources absent, World hashes unchanged, 0 ΔWorld. T3/T5 recovered all 10 unique GOLD M exceedance keys from World. Permit-prose GOLD S semantics were not reused because they were never compiled into World.

### H. Programmability

**MEASURED.** SQL over T1/T4 World expresses NODI partitions matching GOLD E counts and a D-shaped follow-up. Exact GOLD M (28 row-grain exceedances) requires qualifier polarity and a unique applicable limit, which World stores only as codes / candidates. Programmer recovers EPA NODI legend and min/max polarity from stored codes. No portable ABI across the five Worlds.

---

## Cross-domain comparison (high level)

Do not tune NPDES to look like earlier domains.

| | BOM | Diligence | Research | NPDES (this) |
|---|---|---|---|---|
| Kernel changes | none | none | none | **none** |
| Vocabulary | parts/substitutions | identity + contracts | bibliographic | invented NPDES DMR/limit/NODI |
| Mechanical fraction | high structured | mixed | mixed | high structured DMR/limits |
| Semantic frontier | substitution identity | entity identity | (prior) | **permit applicability / monitoring / evidence** |
| Unsupported closure | bounded | gated to 0 on v3.1 | — | **nonzero** (T2 report-only; T3 false exceedance; D NODI 9) |
| Under-closure | — | SAME recall | — | large UNRESOLVED frontiers |
| Grounding | full | full on v3.1 | — | **full** |
| ABI completeness | N/A / later | SATISFIED on v3.1.1 certified | — | fail-closed record, P8 still projects |
| Held-out reuse | D from World | D_WORLD_ONLY exact on certified | — | D runs; exact mixed |
| Programming | World SQL | World SQL | — | World SQL possible; schema unstable |

NPDES is another exercised domain, not arbitrary-domain generality.

---

## Direct answers

1. **Did the frozen semantic kernel survive NPDES without a new primitive?**  
   **Yes.** MEASURED. No primitive added. No kernel counterexample.

2. **Did the constructor invent a useful domain vocabulary without an EPA/NPDES ontology?**  
   **Yes.** MEASURED. Five independent vocabs covering DMR, limits, FY2025 scope, candidates, NODI/no-numeric-result, and purpose judgments. Names unstable; distinctions partially shared.

3. **What proportion of BASE World assertions were mechanical vs semantic?**  
   MEASURED via TaskView origin: ASSERTED is 15–45% of all assertions (T5 996/4506 to T4 3187/7037); the rest DERIVED. OBSERVED (T1 admissions): WORLD mechanical BASE ≈ 1997; WORLD semantic BASE in sqlite ≈ 6 condition tuples. Semantic mass is mostly PURPOSE / UNRESOLVED, not World.

4. **What semantic frontier emerged naturally?**  
   Applicable-limit selection, numeric-comparison eligibility, exceedance, monitoring applicability, missing-evidence, documented no-discharge, permit-stated conditions. Not identity SAME/DISTINCT.

5. **Did P3 discover the time/conditional/report-only/missing-evidence obligations demanded by the purposes?**  
   Partially. MEASURED GOLD S recall 3–9/12. Report-only often found. Staged TDS and source-authority never. Conditional/when-discharging/WET/Delta-BHC inconsistent across trials.

6. **Were any unsupported durable semantic closures admitted?**  
   **Yes.** T2 A report-only→exceedance (10). T3 A mass false exceedance. T1/T3 D: NODI 9→missing required. World itself stayed provenance-accounted; bad closures are purpose outputs / a few WORLD judgment tables (T2 `numeric_exceedance_result`).

7. **Did the system preserve UNRESOLVED where evidence was insufficient?**  
   **Often yes.** T1/T3/T5 C entirely unresolved. T4 A/D conservative. T1 P5: 2345/2776 UNRESOLVED. Correct UNRESOLVED counted as success.

8. **Was every durable World assertion provenance-accounted?**  
   **Yes.** MEASURED ungrounded 0/5 trials.

9. **Did it distinguish operative permit requirements from supporting fact-sheet rationale?**  
   **No, not as a scored authority hierarchy.** MEASURED `S-SOURCE-AUTHORITY` miss 5/5. T4 stores document paths; that is not operative-vs-rationale.

10. **Did it distinguish numeric enforceable limits from report-only monitoring?**  
    **Sometimes.** T4/T5 A: 0 report-only-as-exceedance. T2 A: 10 failures. D: T1/T2 still put report-only keys in exceedance follow-up. `optional_monitoring_flag` is in World.

11. **Did it correctly represent time-dependent/conditional applicability where scored?**  
    **Not for staged TDS** (0/5 P3). Conditional TRC / when-discharging / event-discharge appeared in some frontiers (T1, T5) and were usually left UNRESOLVED rather than correctly closed.

12. **Did NODI/missing evidence remain open-world rather than being forced into compliance/noncompliance?**  
    **Mostly.** NODI C was excluded or unresolved, not called a discharge violation. NODI 9 was sometimes unresolved (T2 D excluded 24 as not_required) and sometimes forced into missing-required (T1/T3 D). Missing was not treated as compliant.

13. **Did ABI `SATISFIED` imply actual materializability with zero invariant violations?**  
    **Yes.** MEASURED 0 violations. `SATISFIED` fields had nonempty bound tables.

14. **Were any purposes correctly marked `INCOMPLETE_PURPOSE`?**  
    **No.** ABI `ok=False` on all trials, but P8 still wrote A/B/C/D JSON. Fail-closed recording without fail-closed projection. Expected incompleteness was expressed as UNRESOLVED rows, not the `INCOMPLETE_PURPOSE` token.

15. **Could held-out D run from World only with sources absent?**  
    **Yes.** MEASURED. Five/five. Isolation leaks 0. Source mentions 0. Sources directory absent.

16. **How much new World construction did D require?**  
    **None.** MEASURED ΔWorld = 0 relations, 0 assertions, hashes unchanged.

17. **Did D reuse semantic state created for A/B/C?**  
    **Mechanical World: yes.** DMR/limit/NODI tables reused. T4 D’s single exceedance matches T4 A. **Permit-prose World: no**, because it was largely never compiled. T1/T2 D re-derived SQL rather than reading A outputs (A/B/C JSON was not in the WORLD_ONLY workspace).

18. **Could ordinary SQL/Python express the intended analyses over World without reconstructing permit/source semantics?**  
    **Partially.** NODI counts and optional-flag joins: yes. Exact exceedance and GOLD S conditionals: no without interpreting qualifier/NODI codes and without staged-limit semantics. See `world_programming.md`.

19. **What was the most important capability failure?**  
    P3/P5 never compiled staged TDS (*10/*11) or source-authority, and usually failed to admit no-discharge / not-required as World relations, so D and SQL cannot compute those GOLD S/E states except by reinterpreting raw NODI/date columns.

20. **Was there any genuine kernel counterexample?**  
    **No.**

21. **Does this experiment justify proceeding to a controlled RAW-vs-WORLD programming benchmark in the NPDES domain?**  
    **Not yet.** Worlds are programmable enough to show the question is live (especially T4), but five incompatible schemas plus incomplete GOLD S World state would confound RAW-vs-WORLD. Freeze one World after interpreting this result. RAW-vs-WORLD was not run.

22. **Scientific status:**

```text
FOURTH_DOMAIN_ARCHITECTURE_SURVIVED
```

**Reasons (architecture survived).** The frozen kernel represented the domain. Constructor v3.1.1 invented coherent NPDES vocabularies without an ontology, compiled grounded Worlds (ungrounded 0), moved the frontier onto permit/monitoring/evidence, fail-closed ABI materializability (0 `SATISFIED` lies), ran held-out D from World only with ΔWorld 0, and supported ordinary SQL for mechanical analyses. No primitive change is required.

**Reasons this is not a capability triumph.** GOLD S staged-TDS and source-authority were never discovered. Unsupported closures occurred (T2 report-only; T3 false exceedance; T1/T3 D NODI 9). ABI incompleteness did not halt P8. Vocabulary/ABI is not portable across trials. Exact A/B/C/D was not required and was not achieved.

Those are constructor capability / campaign-P8 issues. They do not challenge the semantic calculus.

---

## Stop

Constructor v3.1.1 is not repaired here. No P3/P5/prompt/kernel retune. No EPA-specific runtime. No trial rerun with fixes. No RAW-vs-WORLD. No fifth domain.
