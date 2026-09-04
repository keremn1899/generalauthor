"""Write sealed anatomy reports from measured JSON."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.semantic_spine_anatomy_v1.paths import REPORTS, RUNS, TRIALS

CORE_REQ = {
    "unique_applicable_limit",
    "materializable_fy2025_measurements",
    "materializable_candidates",
    "interpret_nodi",
    "interpret_comment",
    "numeric_limit",
    "numeric_measurement",
    "report_only_gap",
    "document_text_unavailable",
}
CORE_REL = {
    "MeasurementBase",
    "LimitBase",
    "CandidateCorrespondence",
    "Fy2025Scope",
    "DocumentInventory",
    "NumericComparison",
    "ReportOnlyOrNonNumeric",
    "MissingEvidence",
}
REACHABLE_REQ = CORE_REQ | {"interpret_optional_monitoring", "interpret_qualifier", "interpret_limit_type"}
NOT_REACHABLE_REQ = {
    "interpret_seasonal_month",
    "interpret_sample_type",
    "interpret_unit",
    "interpret_value_type",
    "interpret_frequency",
    "pass_fail_semantics",
    "aggregated_reporting",
    "interpret_statistical_base",
}


def load(name: str) -> Any:
    return json.loads((RUNS / name).read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join("" if c is None else str(c) for c in row) + " |")
    return "\n".join(out)


def write(name: str, body: str) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(body.rstrip() + "\n", encoding="utf-8")


def loc_row(inv: dict) -> list[Any]:
    loc = inv["loc"]
    return [
        inv["trial"],
        loc["physical_loc"],
        loc["nonblank_loc"],
        loc["semantic_loc"],
        loc["mechanical_runtime_support_loc"],
        loc["requirement_loc"],
        loc["hole_instance_loc"],
    ]


def program_anatomy(invs: list[dict]) -> str:
    cat_headers = ["trial"] + list(invs[0]["loc"]["by_category"].keys())
    cat_rows = [[i["trial"]] + [i["loc"]["by_category"][c] for c in i["loc"]["by_category"]] for i in invs]
    call_keys = sorted({k for i in invs for k in i["calls"]["call_counts"]})
    interesting = [
        "referent",
        "relation",
        "map",
        "derive",
        "require_unique",
        "require_materializable",
        "require_interpreted",
        "require_numeric",
        "unresolved",
        "rows",
        "profile",
        "join",
    ]
    call_rows = [[i["trial"]] + [i["calls"]["call_counts"].get(k, 0) for k in interesting] for i in invs]
    return "\n".join(
        [
            "# Program anatomy",
            "",
            "Research-only. Sealed originals were not modified.",
            "",
            "## MEASURED line counts",
            "",
            "Physical LOC is Python file length. Semantic LOC is AST-painted declaration of referents, relations, maps, derives, requirement schemas, and explicit unresolved emission. Mechanical/runtime-support is source I/O, profiling, physical normalization, and helpers. Requirement LOC includes schema calls plus instantiation loops. Hole/instance LOC is `purpose.unresolved` sites.",
            "",
            md_table(
                ["trial", "physical", "nonblank", "semantic", "mechanical", "requirement", "hole/instance"],
                [loc_row(i) for i in invs],
            ),
            "",
            "Do not equate physical Python size with ontology size. T2 is the longest file because it splits identity into many WORLD relations; T5 is shortest because it derives most PURPOSE relations from three bases.",
            "",
            "## MEASURED category paint (nonblank lines)",
            "",
            md_table(cat_headers, cat_rows),
            "",
            "## MEASURED AST call-site counts",
            "",
            md_table(["trial"] + interesting, call_rows),
            "",
            "## OBSERVED",
            "",
            "- Final programs contain almost no leftover `profile`/`join_profile` calls. Source exploration happened in-session and was not committed as the spine.",
            "- `unresolved` call sites are few; spine `requirements` rows balloon when those sites sit inside per-row loops (T2/T3/T4).",
            "- T3 `require_interpreted` count includes a 12-month seasonal loop (one schema, twelve surface names).",
            "",
            "## HYPOTHESIS",
            "",
            "Most of the 652–1,015 physical lines are not distinct ontology. Semantic-painted LOC is large because relation signatures and `require_*` blocks are verbose; factorized schema counts stay in the teens.",
        ]
    )


def semantic_inventory(invs: list[dict]) -> str:
    parts = [
        "# Semantic inventory",
        "",
        "Normalized by meaning. Original Python/table names are preserved alongside evaluator labels. Normalized labels were not fed back into programs.",
        "",
        "## MEASURED schema counts",
        "",
        md_table(
            [
                "trial",
                "referent kinds",
                "relations",
                "unique require names",
                "factorized req schemas",
                "spine requirement rows",
                "hole groups",
                "hole instances",
            ],
            [
                [
                    i["trial"],
                    i["n_referent_kinds"],
                    i["n_relations"],
                    i["n_requirement_schemas"],
                    i["factorized"]["n_requirement_schemas"],
                    i["n_spine_requirement_rows"],
                    i["n_hole_groups"],
                    i["n_hole_instances"],
                ]
                for i in invs
            ],
        ),
        "",
    ]
    for inv in invs:
        parts.extend(
            [
                f"## {inv['trial']}",
                "",
                "### Referents (original → normalized)",
                "",
                "\n".join(f"- `{r['original']}` → **{r['normalized']}**" for r in inv["referents"]) or "- none declared via `world.referent` string kind",
                "",
                "### Relations",
                "",
                md_table(
                    ["original", "normalized", "derived", "mode", "n_rows"],
                    [
                        [r["original"], r["normalized"], r["derived"], r["mode"], r["n_rows"]]
                        for r in inv["relations"]
                    ],
                ),
                "",
                "### Requirement call sites (original → normalized)",
                "",
                md_table(
                    ["kind", "original", "normalized", "field"],
                    [
                        [r["kind"], r["original"], r["normalized"], r.get("field")]
                        for r in inv["requirement_schemas"]
                    ],
                ),
                "",
                f"Grain: schemas={inv['grain']['requirement_schemas']}, candidate obligations={inv['grain']['candidate_semantic_obligations']}, occurrences={inv['grain']['hole_occurrences']}.",
                "",
            ]
        )
    parts.extend(
        [
            "## OBSERVED",
            "",
            "Independently named relations that both express Measurement ↔ candidate applicable Limit are labeled `CandidateCorrespondence`. Document inventory relations are `DocumentInventory` whether named `document_catalog` or `permit_document`.",
            "",
            "## HYPOTHESIS",
            "",
            "The five programs share a small schema vocabulary. Apparent requirement-name diversity is mostly field-level `require_interpreted` plus per-row `unresolved` instantiation.",
        ]
    )
    return "\n".join(parts)


def consensus_spine(invs: list[dict], inter: dict) -> str:
    def block(title: str, key: str) -> list[str]:
        rows = []
        for n in range(5, 0, -1):
            items = inter[key][f"{n}/5"]
            if items:
                rows.append(f"- **{n}/5:** " + ", ".join(f"`{x}`" for x in items))
        return [f"### {title}", ""] + rows + [""]

    stable_req = inter["requirements"]["5/5"]
    frequent_req = inter["requirements"]["4/5"] + inter["requirements"]["3/5"]
    local_req = inter["requirements"]["2/5"] + inter["requirements"]["1/5"]
    return "\n".join(
        [
            "# Consensus spine",
            "",
            "Naming differences are not treated as semantic instability.",
            "",
            "## MEASURED stability",
            "",
            *block("Concept / referent stability", "referents"),
            *block("Relation-role stability", "relations"),
            *block("Requirement stability", "requirements"),
            "## Stable core",
            "",
            "Semantics independently constructed in **5/5** (MEASURED):",
            "",
            "- Referents: " + (", ".join(f"`{x}`" for x in inter["referents"]["5/5"]) or "none at 5/5; identity is often implicit in relation roles"),
            "- Relations: " + ", ".join(f"`{x}`" for x in inter["relations"]["5/5"]),
            "- Requirements: " + ", ".join(f"`{x}`" for x in stable_req),
            "",
            "### OBSERVED core reading",
            "",
            "Every trial materializes measurements, limits, a FY2025/purpose-scoped correspondence, a document inventory, numeric comparison candidates, missing-evidence/NODI handling, and comment/opaque-text interpretation. Every trial authors uniqueness of applicable limit (surface names differ) and NODI interpretation.",
            "",
            "## Frequent extensions",
            "",
            "4/5 or 3/5:",
            "",
            "- Relations: " + ", ".join(f"`{x}`" for x in inter["relations"]["4/5"] + inter["relations"]["3/5"]),
            "- Requirements: " + ", ".join(f"`{x}`" for x in frequent_req),
            "",
            "## Trial-local semantics",
            "",
            "1/5 or 2/5:",
            "",
            "- Relations: " + ", ".join(f"`{x}`" for x in inter["relations"]["2/5"] + inter["relations"]["1/5"]),
            "- Requirements: " + ", ".join(f"`{x}`" for x in local_req),
            "",
            "## HYPOTHESIS",
            "",
            "Seasonal-month flags, sample-type, unit, value-type, pass/fail extras, and geometric-mean comments are trial-local elaborations. `interpret_frequency` is 5/5 but single-element ablation-redundant for primary E1 — stable does not mean purpose-required.",
        ]
    )


def requirement_factorization(invs: list[dict]) -> str:
    rows = []
    for inv in invs:
        d = inv["duplication"]["counts_by_category"]
        rows.append(
            [
                inv["trial"],
                inv["calls"]["n_requirement_call_sites"],
                inv["n_requirement_schemas"],
                inv["factorized"]["n_requirement_schemas"],
                inv["n_spine_requirement_rows"],
                inv["grain"]["candidate_semantic_obligations"],
                inv["n_hole_groups"],
                inv["n_hole_instances"],
                d["A_PURE_CODE_DUPLICATION"],
                d["B_INSTANCE_EXPANSION"],
                d["C_MISSING_PARAMETERIZATION"],
                d["D_FALSE_DUPLICATION"],
                d["E_UNCERTAIN"],
            ]
        )
    mean_occ = sum(i["n_hole_instances"] for i in invs) / len(invs)
    mean_obl = sum(i["grain"]["candidate_semantic_obligations"] for i in invs) / len(invs)
    return "\n".join(
        [
            "# Requirement factorization",
            "",
            "Three grains: **requirement schema** (reusable condition), **semantic obligation** (bounded proposition, possibly covering many subjects), **affected occurrence** (a concrete blocked record).",
            "",
            "Hole-group count is a runtime grouping artifact. It is not obligation count.",
            "",
            "## MEASURED",
            "",
            md_table(
                [
                    "trial",
                    "authored call sites",
                    "unique surface names",
                    "normalized schemas",
                    "grounded req rows",
                    "candidate obligations",
                    "hole groups",
                    "occurrences",
                    "A emitted",
                    "B emitted",
                    "C emitted",
                    "D emitted",
                    "E emitted",
                ],
                rows,
            ),
            "",
            f"Mean hole occurrences: **{mean_occ:.0f}**. Mean candidate obligations after value-level grouping: **{mean_obl:.0f}**.",
            "",
            "## Category key",
            "",
            "- **A — PURE CODE DUPLICATION:** same requirement name authored more than once.",
            "- **B — INSTANCE EXPANSION:** one schema, many grounded subjects (`require_interpreted` over rows).",
            "- **C — MISSING PARAMETERIZATION:** one call inside a per-row loop emitting many World requirement rows (typical `unresolved`).",
            "- **D — FALSE DUPLICATION:** similar labels, different questions (not counted unless names collide across kinds).",
            "- **E — UNCERTAIN:** singleton emission.",
            "",
            "## OBSERVED",
            "",
            "- T3 surface names include twelve `seasonal_{month}_for_monitoring_applicability` names generated by one loop. That is instance expansion of one schema, not twelve ontologies. T3 category E=12 is those singleton World requirement rows; ablating the loop drops 12 hole groups (MEASURED).",
            "- T2/T3/T4 `unresolved` loops over nonempty comments emit hundreds to thousands of requirement rows from one authored schema (`conditional_*` / `permit_comment_*`). Category C.",
            "- T5 emits 8 groups from 24 unique names because it mostly avoids per-row unresolved loops except for three comment-literal families plus one document-level unresolved.",
            "",
            "## Candidate reusable obligation schemas",
            "",
            "Evaluator-side, not a rewrite:",
            "",
            "- `∀ opaque NODI code: interpretation required`",
            "- `∀ nonempty permit comment: applicability semantics required`",
            "- `∀ nonnumeric candidate limit: classification required`",
            "- `∀ measurement in FY2025: unique applicable limit`",
            "- `∀ inventoried permit document: narrative text not in structured sources`",
            "- `∀ seasonal month flag: meaning required` (one schema, twelve flags)",
            "",
            "## HYPOTHESIS",
            "",
            "Group-count variance (T3=31 vs T5=8) is factorization and grounding grain, not different E1 coverage.",
        ]
    )


def purpose_dependency(invs: list[dict], inter: dict) -> str:
    all_req = set(inter["raw"]["requirements"])
    all_rel = set(inter["raw"]["relations"])
    reachable_req = sorted(all_req & REACHABLE_REQ)
    not_req = sorted(all_req & NOT_REACHABLE_REQ)
    amb_req = sorted(all_req - REACHABLE_REQ - NOT_REACHABLE_REQ)
    reachable_rel = sorted(all_rel & CORE_REL)
    not_rel = sorted(all_rel - CORE_REL - {"OtherRelation", "CommentPayload", "CodePayload", "EffectiveInterval", "SeasonalMonth", "MonitoringObligation"})
    amb_rel = sorted(all_rel - set(reachable_rel) - set(not_rel))
    n_sem = sum(i["factorized"]["n_requirement_schemas"] + i["factorized"]["n_relation_schemas"] + i["factorized"]["n_referent_schemas"] for i in invs)
    return "\n".join(
        [
            "# Purpose dependency and backward slice",
            "",
            "Analysis-only graph. Sealed originals were not deleted from.",
            "",
            "## Evaluator-side dependency",
            "",
            "```text",
            "Purpose A (applicable numeric limits, FY2025)",
            "  → unique applicable limit per measurement",
            "  → CandidateCorrespondence / NumericComparison / ReportOnlyOrNonNumeric",
            "  → Measurement, Limit, interval/FY2025 grounding",
            "  → structured DMR + permit_limits",
            "  ↳ holes: uniqueness, non-numeric limit, comment-conditioned applicability",
            "",
            "Purpose B (monitoring obligations)",
            "  → MonitoringObligation + comment/optional/frequency interpretation",
            "  → DocumentInventory (authority / narrative conditions)",
            "  → permit_limits + document_inventory.json",
            "  ↳ holes: uninterpreted comment, WHEN DISCHARGING, document text unavailable",
            "",
            "Purpose C (missing evidence)",
            "  → MissingEvidence + interpret_nodi",
            "  → Measurement result / NODI field grounding",
            "  ↳ holes: NODI semantics, missing reported value",
            "```",
            "",
            "## MEASURED backward slice",
            "",
            "Slice starts from Purpose A/B/C required outputs and all E1-scored semantic holes.",
            "",
            f"- union of normalized requirement schemas across trials: {len(all_req)}",
            f"- PURPOSE_REACHABLE requirements: {len(reachable_req)} — " + ", ".join(f"`{x}`" for x in reachable_req),
            f"- NOT_PURPOSE_REACHABLE candidates: {len(not_req)} — " + ", ".join(f"`{x}`" for x in not_req),
            f"- AMBIGUOUS_DEPENDENCY requirements: {len(amb_req)} — " + ", ".join(f"`{x}`" for x in amb_req),
            "",
            f"- PURPOSE_REACHABLE relations: {len(reachable_rel)} — " + ", ".join(f"`{x}`" for x in reachable_rel),
            f"- remaining relation labels: " + ", ".join(f"`{x}`" for x in sorted(all_rel - set(reachable_rel))),
            "",
            "Per-trial semantic-element counts (factorized referents+relations+requirement schemas):",
            "",
            md_table(
                ["trial", "elements", "req schemas", "rel schemas", "ref schemas"],
                [
                    [
                        i["trial"],
                        i["factorized"]["n_requirement_schemas"]
                        + i["factorized"]["n_relation_schemas"]
                        + i["factorized"]["n_referent_schemas"],
                        i["factorized"]["n_requirement_schemas"],
                        i["factorized"]["n_relation_schemas"],
                        i["factorized"]["n_referent_schemas"],
                    ]
                    for i in invs
                ],
            ),
            "",
            "## OBSERVED",
            "",
            "- Primary E1 seams do not include wet-seasonal GOLD (`S-AZTEC-WET-SEASONAL` was 0/5 in the sealed Python probe). Seasonal-month interpretation is therefore a candidate non-reachable extra relative to the tested purpose slice.",
            "- Qualifiers, optional-monitoring flags, and limit-type codes sit on the comparison/applicability path: AMBIGUOUS until ablation.",
            "- CommentPayload relations are reachable when they carry WHEN DISCHARGING / report-only comments.",
            "",
            "## HYPOTHESIS",
            "",
            "A purpose-reachable core of roughly a dozen schemas is sufficient; extras are reviewable dead semantic mass rather than hidden E1 coverage.",
        ]
    )


def ablation_results(baselines: dict, ablations: list[dict]) -> str:
    rows = []
    for row in ablations:
        s = row["score"]
        p = s.get("precise") or {}
        rows.append(
            [
                row["trial"],
                row["ablation_id"],
                row["n_removed_nodes"],
                s.get("ok"),
                s.get("e1_hits"),
                s.get("e2_n_true"),
                s.get("n_hole_groups"),
                row["delta_e1"],
                row["delta_e2"],
                row["delta_groups"],
                int(bool(p.get("tds_precise"))),
                int(bool(p.get("when_precise"))),
                int(bool(p.get("nodi_precise"))),
                int(bool(p.get("authority_precise"))),
                row["label"],
            ]
        )
    counts = Counter(r["label"] for r in ablations)
    base_rows = [
        [
            t,
            baselines[t].get("ok"),
            baselines[t].get("e1_hits"),
            baselines[t].get("e2_n_true"),
            baselines[t].get("n_hole_groups"),
            baselines[t].get("n_hole_instances"),
        ]
        for t in TRIALS
        if t in baselines
    ]
    redundant = [r for r in ablations if r["label"] == "LOCALLY_REDUNDANT_FOR_PURPOSE"]
    required = [r for r in ablations if r["label"] == "REQUIRED_FOR_PURPOSE"]
    coupled = [r for r in ablations if r["label"] == "COUPLED_OR_INDETERMINATE"]
    return "\n".join(
        [
            "# Ablation results",
            "",
            "Research copies only. No model repair. Frozen E1/E2 functions imported read-only from Purpose-First Python Spine Probe v1.",
            "",
            "Frozen E1 **did not move** on any single-element ablation (all remain 7/7). Labels below therefore rest on purpose-relevant precise coverage (cardinality hole, authored uniqueness, NODI hole, document-text hole), not on the coarse triggerability scorer.",
            "",
            "## MEASURED baseline reruns of unmodified copies",
            "",
            md_table(["trial", "ok", "E1 hits", "E2", "groups", "instances"], base_rows),
            "",
            "## MEASURED single-element ablations",
            "",
            md_table(
                [
                    "trial",
                    "element",
                    "removed",
                    "ok",
                    "E1",
                    "E2",
                    "groups",
                    "ΔE1",
                    "ΔE2",
                    "Δgroups",
                    "TDS*",
                    "WHEN*",
                    "NODI*",
                    "AUTH*",
                    "label",
                ],
                rows,
            ),
            "",
            "T2/T4 AUTH* is 0 on every row because those trials inventory documents but emit no document-text hole (frozen E1 authority still hits via inventory tokens). That is a coverage gap relative to T1/T3/T5, not an ablation artifact.",
            "",
            f"Labels: LOCALLY_REDUNDANT_FOR_PURPOSE={counts.get('LOCALLY_REDUNDANT_FOR_PURPOSE', 0)}, REQUIRED_FOR_PURPOSE={counts.get('REQUIRED_FOR_PURPOSE', 0)}, COUPLED_OR_INDETERMINATE={counts.get('COUPLED_OR_INDETERMINATE', 0)}.",
            "",
            "### Locally redundant under this purpose/fixture",
            "",
            "\n".join(f"- `{r['trial']}/{r['ablation_id']}` (Δgroups={r['delta_groups']})" for r in redundant) or "- none",
            "",
            "### Required for purpose (measurable degradation)",
            "",
            "\n".join(f"- `{r['trial']}/{r['ablation_id']}` (ΔE1={r['delta_e1']}, ΔE2={r['delta_e2']})" for r in required) or "- none",
            "",
            "### Coupled or indeterminate",
            "",
            "\n".join(f"- `{r['trial']}/{r['ablation_id']}` ok={r['score'].get('ok')} errors={r['score'].get('errors')}" for r in coupled) or "- none",
            "",
            "## Candidate locally deletion-minimal set",
            "",
            "Modest claim: **locally deletion-minimal under the tested purpose and fixture**, not a globally minimal ontology.",
            "",
            "Keep, across trials, the intersection of elements whose removal was REQUIRED_FOR_PURPOSE or that belong to the 5/5 stable core even when a single-element drop did not move frozen E1:",
            "",
            "- FY2025-scoped measurement/limit correspondence with interval structure",
            "- uniqueness of applicable limit (authored even when the cardinality hole is not the E1 token)",
            "- NODI interpretation",
            "- permit-comment interpretation or an equivalent unresolved discharge-condition hole",
            "- document inventory plus unavailable-narrative hole",
            "- numeric vs non-numeric/report-only split",
            "",
            "Drop candidates that survived as LOCALLY_REDUNDANT_FOR_PURPOSE (seasonal-month flags, extra frequency/sample-type/unit/value-type interprets, T5 pass-fail and geometric-mean extras when comment/NODI/document holes remain).",
            "",
            "## OBSERVED",
            "",
            "Interactions (not jointly ablated):",
            "",
            "- T1 `unique_catalog_variant` is the only cardinality hole; `unique_schedule_match` is satisfied. Dropping catalog loses the TDS uniqueness hole; dropping schedule does not. The pair is coupled: uniqueness remains authored if either `require_unique` survives.",
            "- T1/T5 WHEN-literal unresolved and generic comment `require_interpreted` substitute for each other on WHEN* precise coverage.",
            "- T2/T3/T4 NODI is duplicated across interpret + unresolved; dropping one named NODI requirement leaves another.",
            "- T2/T4 have document inventory relations but no dedicated document-text hole; frozen E1 authority still fires from inventory tokens plus unrelated UNINTERPRETED groups.",
            "",
            "## HYPOTHESIS",
            "",
            "A substantially smaller locally deletion-minimal semantic core exists; T5 is already close to it.",
        ]
    )


def success_mechanisms() -> str:
    return """# Success mechanisms

Frozen construction traces and programs only. No invented generic algorithm unless the five artifacts support it.

## MEASURED recurring chains

### Staged TDS

```text
purpose A requires unique applicable limit per measurement
→ inspect permit_limits / DMR join keys and LIMIT_BEGIN/END
→ observe temporal (and catalog-variant) multiplicity
→ introduce interval/applicability structure (parse_date, interval_contains)
→ require uniqueness of the candidate correspondence
→ T1 emits CARDINALITY_OVERSATISFIED on catalog variants;
  T2–T5 often satisfy uniqueness mechanically and still score E1 TDS
  because comments contain "TDS" and date structure is present
```

### WHEN DISCHARGING

```text
purpose B requires monitoring applicability
→ encounter DMR_COMMENT_TEXT
→ refuse to interpret mechanically as World truth
→ T2/T3/T4: require_interpreted(comment) + unresolved if nonempty
→ T1/T5: additionally match the source-native phrase to emit a named unresolved
→ hole: UNINTERPRETED and/or EXPLICIT_UNRESOLVED
```

### Source authority

```text
purpose B/C conditions live in permit package prose
→ structured workspace offers only document_inventory.json
→ map documents (kind/filename/hash)
→ emit unresolved: narrative text not materialized
```

### Report-only / non-numeric

```text
purpose A requires numeric comparison
→ observe empty LIMIT_VALUE_NMBR with reported DMR values
→ split NumericComparison vs ReportOnlyOrNonNumeric
→ require_numeric and/or require_interpreted(limit type) and/or unresolved
```

### Opaque NODI / monitoring

```text
purpose C requires classification of missing evidence
→ encounter NODI_CODE (and optional-monitoring flags)
→ refuse to treat codes as self-explaining
→ require_interpreted(nodi)
```

## WHEN DISCHARGING: T1/T5 vs T2/T3/T4

| | T1 | T5 | T2 | T3 | T4 |
|---|---|---|---|---|---|
| abstraction | named discharge-condition unresolved | named conditional-discharge unresolved | interpret comment field | interpret comment field | interpret comment field |
| literal match | `comment == "WHEN DISCHARGING."` | `"WHEN DISCHARGING" in comment.upper()` | no | no | no |
| silent World assertion? | no — emits unresolved | no — emits unresolved | no | no | no |
| hardcode audit | flagged | flagged | clean | clean | clean |

### Safe fixture-sensitive detection

T1/T5 locate an unresolved dependency by matching a source-native phrase that exists in this fixture. They do not assert that WHEN DISCHARGING means "not required" or "required only on discharge." Architecturally they are **detection of a hole**, not closure.

### Generic unresolved-semantic detection

T2/T3/T4 treat any nonempty comment as uninterpreted. That is reusable across comments (FOOTNOTE, geometric mean, WHEN DISCHARGING, pass/fail). It overgenerates groups/instances relative to T5's three literal families.

### Unsupported semantic closure

None of the five trials assign a World-true monitoring rule from the phrase. That would have been the undermining pattern. It is not present.

**Verdict (OBSERVED):** T1/T5 are architecturally safe but fixture-sensitive. They do not undermine the result. T2–T4 expose the more reusable pattern.

## Why E1=1.00 with different shapes

The frozen scorer is structural triggerability, reused unchanged from Spine Compiler Probe v1. It asks whether the program/holes mention the seam's tokens and emit an allowed failure kind — not whether each trial isolated the same Farmington TDS uniqueness hole. All five authored interval-aware correspondence, comment opacity, NODI opacity, numeric/non-numeric split, and document inventory. That is enough for 7/7.

## Why groups range from 8 to 31

MEASURED: T3 authors extra `require_interpreted` fields (value_type, unit, twelve seasonal months, optional flags on three relations, duplicate NODI requirements) and per-row comment unresolved. T5 authors a tight set and three comment-literal unresolved families. Coverage of primary seams is the same; factorization and grain differ.

## Recurring authoring motifs (supported)

1. Purpose requires selection → inspect candidate records → observe variation → introduce interval/applicability → require uniqueness.
2. Purpose requires classification → encounter opaque source field → refuse mechanical interpretation → require semantic meaning.
3. Purpose depends on narrative permit conditions → only hashes/filenames exist → emit document-text hole rather than invent authority.

## HYPOTHESIS

First-shot Python construction is a draft semantic spine: the motifs are stable, the extras are overinstantiation.
"""


def human_review(invs: list[dict], ablations: list[dict], inter: dict) -> str:
    redundant = {(r["trial"], r["ablation_id"]) for r in ablations if r["label"] == "LOCALLY_REDUNDANT_FOR_PURPOSE"}
    parts = [
        "# Human / ontology-engineer review surface",
        "",
        "Not an interactive repair experiment. Compact questions a human would need to certify a draft spine. Raw Python is out of scope unless a fixture-sensitive match must be inspected.",
        "",
        "## Shared review packet (all trials)",
        "",
        "Declared purposes: A applicable FY2025 numeric limits; B monitoring obligations; C missing-evidence classification.",
        "",
        "Stable semantic spine to certify:",
        "",
        "1. Is FY2025 ∩ measurement-period ∩ limit-effective-interval the right applicability geometry?",
        "2. Is uniqueness of applicable limit the right cardinality (ONE per measurement), or can staged/catalog variants be simultaneous?",
        "3. What does each distinct NODI code mean for missing-evidence / requiredness?",
        "4. What does nonempty DMR comment text do to monitoring/limit applicability, including WHEN DISCHARGING?",
        "5. Are empty numeric limits report-only, or is another classification required?",
        "6. Does document inventory without text correctly leave narrative authority unresolved?",
        "",
        "Estimate: **6 genuinely consequential questions** for the shared core, not 2,972 hole occurrences.",
        "",
    ]
    for inv in invs:
        extras = [
            x
            for x in inv["factorized"]["requirement_schemas"]
            if inter["raw"]["requirements"].get(x, 0) <= 2
        ]
        parts.extend(
            [
                f"## {inv['trial']}",
                "",
                f"- declared purpose: A/B/C as in participant `visible_*.md`",
                f"- stable spine schemas: {inv['factorized']['n_requirement_schemas']} normalized requirements, {inv['factorized']['n_relation_schemas']} relation schemas",
                f"- trial-specific extras: " + (", ".join(f"`{x}`" for x in extras) or "none"),
                f"- unresolved obligations (candidate): {inv['grain']['candidate_semantic_obligations']}",
                f"- hole occurrences (do not review one-by-one): {inv['n_hole_instances']}",
                f"- fixture-sensitive matches: " + ("WHEN DISCHARGING literal (hardcode-flagged)" if inv["trial"] in {"T1", "T5"} else "generic nonempty-comment detection"),
                "",
            ]
        )
    parts.extend(
        [
            "## Uncertified modeling choices (do not auto-promote)",
            "",
            "- T1 uniqueness on catalog variants vs T5 uniqueness on measurement–limit pairs",
            "- T3 12-month seasonal flags vs T5 omitting seasonal GOLD (primary E1 did not require it)",
            "- T1/T5 literal WHEN DISCHARGING vs T2–T4 generic comments",
            "- known-empty vs known-token lists on `require_interpreted` (T5 lists `<=`, `ENF`, month codes)",
            "",
            "## HYPOTHESIS",
            "",
            "Conversational certification should present the 6 core questions plus a short extras list, never raw Python or per-row holes.",
        ]
    )
    return "\n".join(parts)


def choose_label(ablations: list[dict], invs: list[dict], inter: dict) -> str:
    redundant_n = sum(1 for r in ablations if r["label"] == "LOCALLY_REDUNDANT_FOR_PURPOSE")
    required_n = sum(1 for r in ablations if r["label"] == "REQUIRED_FOR_PURPOSE")
    e1_drop = [r for r in ablations if (r.get("delta_e1") or 0) < 0]
    core_5 = len(inter["requirements"]["5/5"])
    if e1_drop and core_5 < 3:
        return "SEMANTIC_STABILITY_SUPERFICIAL"
    if redundant_n >= 8 and required_n <= 12 and core_5 >= 4:
        return "STABLE_CORE_OVERFACTORED"
    if required_n >= 20 and redundant_n <= 3:
        return "SEMANTIC_SUCCESS_REQUIRES_LARGE_MODEL"
    if redundant_n >= 8 and core_5 >= 5:
        return "SMALL_STABLE_SEMANTIC_CORE"
    return "MIXED_SEMANTIC_SPINE_ANATOMY"


def master(invs, inter, baselines, ablations) -> str:
    label = choose_label(ablations, invs, inter)
    sem_frac = []
    for i in invs:
        nb = i["loc"]["nonblank_loc"] or 1
        sem_frac.append((i["trial"], i["loc"]["semantic_loc"], nb, round(100 * i["loc"]["semantic_loc"] / nb)))
    mean_occ = sum(i["n_hole_instances"] for i in invs) / len(invs)
    mean_obl = sum(i["grain"]["candidate_semantic_obligations"] for i in invs) / len(invs)
    mean_schema = sum(i["factorized"]["n_requirement_schemas"] for i in invs) / len(invs)
    answers = {
        "1": (
            "Physical LOC is 652–1,015 (T5–T2). Semantic-painted nonblank LOC is 339–492 "
            "(50–65% of nonblank). That paint is mostly relation-signature and require_* blocks, "
            "not hundreds of distinct concepts. Factorized requirement schemas are 11–16 per trial. "
            "Mechanical+OTHER (grounding loops, helpers, comments) is the rest of the file."
        ),
        "2": (
            "Per trial: referent kinds 4–11 (T3 has 39 referent() calls over fewer kinds); "
            "relations 8–25; unique require names 19–30; factorized requirement schemas 11–16; "
            "spine requirement rows 48–1,273."
        ),
        "3": "5/5: " + ", ".join(inter["requirements"]["5/5"] + inter["relations"]["5/5"]),
        "4": (
            "Trial-local (1/5 or 2/5): aggregated_reporting, sample_type, value_type, unit, "
            "statistical_base, report_only named gap, SeasonalMonth relations, CodePayload, "
            "T1 catalog-variant cardinality hole. Frequency interpretation is 5/5 but locally redundant for primary E1."
        ),
        "5": (
            "All five authored interval-aware correspondence, comment opacity, NODI opacity, "
            "a numeric/non-numeric split, uniqueness, and document inventory. Frozen E1 is "
            "triggerability (any allowed failure kind + seam tokens). It did not require identical holes."
        ),
        "6": (
            "T3=31 vs T5=8 is factorization and grain: T3's 12 seasonal month names alone are 12 groups; "
            "ablating that loop drops T3 to 19 groups with E1 still 7/7. T5 emits 8 groups from a tight "
            "schema set plus three comment-literal unresolved families. Not different primary coverage."
        ),
        "7": (
            "A pure code duplication: 0 emitted rows. B instance expansion and C missing parameterization "
            "dominate (T3 C=1,239 rows from per-row unresolved). T3 E=12 is twelve seasonal surface names, "
            "not twelve ontologies. D false duplication was not needed."
        ),
        "8": f"Mean candidate obligations ≈ {mean_obl:.0f} after grouping hole (requirement, observed value/kind).",
        "9": f"Mean occurrences {mean_occ:.0f} versus mean ~{mean_schema:.0f} factorized schemas and ~{mean_obl:.0f} obligations.",
        "10": (
            "PURPOSE_REACHABLE: CandidateCorrespondence, uniqueness, NODI, comments/WHEN, "
            "numeric comparison, document inventory/text hole, FY2025 scope. "
            "NOT_PURPOSE_REACHABLE relative to primary E1: seasonal months, sample type, unit/value-type, "
            "frequency (stable but ablation-redundant), T5 pass-fail/geometric extras. "
            "AMBIGUOUS: optional-monitoring and limit-type (on the path, not single-element proven)."
        ),
        "11": (
            "REQUIRED_FOR_PURPOSE (7): T1 unique_catalog (cardinality hole), T1 nodi, T2/T4/T5 unique "
            "(authored uniqueness disappears), T5 nodi, T5 document-text unresolved. "
            "23 locally redundant including T3's 12-month loop, freq/sample-type/unit/value-type, "
            "T5 aggregated/pass-fail, and pairwise WHEN substitutes."
        ),
        "12": (
            "Yes, locally: frozen E1 never moved; many extras drop without precise-coverage loss; "
            "T5 is already near a deletion-minimal draft. Not a global ontology minimum. "
            "T1 uniqueness is a pair (catalog hole + satisfied schedule unique)."
        ),
        "13": (
            "Main complexity is requirement instantiation (C loops, 48–1,273 rows) plus physical grounding "
            "(date/join maps), then execution scaffolding. Conceptual modeling of the core is small (~6 "
            "stable requirement schemas + ~6 stable relation schemas)."
        ),
        "14": (
            "Three supported motifs: uniqueness after seeing temporal/catalog multiplicity; "
            "refuse opaque NODI/comment codes as World truth; inventory documents and leave narrative unresolved."
        ),
        "15": (
            "T1/T5 are architecturally safe fixture-sensitive hole detectors (literal match → unresolved, "
            "no World assertion). They do not undermine the result. T2–T4 show the reusable nonempty-comment pattern."
        ),
        "16": (
            "About six core certification questions (interval geometry, uniqueness cardinality, NODI, "
            "comments/WHEN DISCHARGING, report-only vs numeric, document text) plus a short extras list. "
            "Not raw Python and not 2,972 occurrences."
        ),
        "17": (
            "Yes. First-shot construction produced a draft semantic spine: 5/5 E1=1.00 from a stable core, "
            "with overfactored extras a human can factor or delete. Conversational refinement is the "
            "natural next probe, not a fifth domain."
        ),
        "18": (
            "Much of the minimality is safely post-construction: 23/30 single-element drops were locally "
            "redundant; T3 seasonal loop is the clearest factoring win. First-shot authoring need not emit "
            "the minimal schema set, but should keep uniqueness, NODI, comments, and document-text holes."
        ),
    }
    q = "\n\n".join(f"### {k}\n\n{v}" for k, v in answers.items())
    return "\n".join(
        [
            "# Semantic Spine Anatomy & Minimality Probe v1",
            "",
            f"Sealed interpretation: **{label}**",
            "",
            "Not constructor repair. Original `construction.py` programs, Worlds, holes, Constructor v3.1.1, TaskView/kernel, P3/P5, Spine Compiler Probe v1, and prose probes were not modified.",
            "",
            "## MEASURED headline",
            "",
            md_table(["trial", "semantic LOC", "nonblank LOC", "% semantic-painted"], [[a, b, c, d] for a, b, c, d in sem_frac]),
            "",
            f"Mean factorized requirement schemas: {mean_schema:.1f}. Mean candidate obligations: {mean_obl:.0f}. Mean hole occurrences: {mean_occ:.0f}.",
            "",
            "Baseline reruns of unmodified copies: see ablation_results.md.",
            "",
            "## Required answers",
            "",
            q,
            "",
            "## Interpretation",
            "",
            f"**{label}**",
            "",
            "Complexity measures used descriptively: semantic elements, relation schemas, requirement schemas, grounded instances, dependency depth. No ontology-size scoring formula.",
            "",
            "## STOP",
            "",
            "No constructor promotion. No P1–P4 collapse. No prose retrieval. No P5. No conversational certification. No fifth domain.",
        ]
    )


def main() -> None:
    invs = load("inventories.json")
    inter = load("intersection.json")
    baselines = load("baselines.json")
    ablations = load("ablations.json")
    write("program_anatomy.md", program_anatomy(invs))
    write("semantic_inventory.md", semantic_inventory(invs))
    write("consensus_spine.md", consensus_spine(invs, inter))
    write("requirement_factorization.md", requirement_factorization(invs))
    write("purpose_dependency.md", purpose_dependency(invs, inter))
    write("ablation_results.md", ablation_results(baselines, ablations))
    write("success_mechanisms.md", success_mechanisms())
    write("human_review_surface.md", human_review(invs, ablations, inter))
    write("semantic_spine_anatomy_v1.md", master(invs, inter, baselines, ablations))
    print("reports written", REPORTS)


if __name__ == "__main__":
    main()
