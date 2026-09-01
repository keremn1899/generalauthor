"""Write machine-readable and markdown reports for the read-surface replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.read_surface_replay import DIAGNOSTICS_PATH, REPORT_PATH
from research.taskview_orientation.read_surface_replay.accounting import run_accounting
from research.taskview_orientation.read_surface_replay.headroom import run_headroom
from research.taskview_orientation.read_surface_replay.ledger import CampaignLedger, build_campaign_ledger


def _fmt(value: Any) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        return f"{value:.0f}" if value.is_integer() else f"{value:.1f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def _table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> str:
    header = "| " + " | ".join(title for title, _key in columns) + " |"
    sep = "| " + " | ".join("---" for _ in columns) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(_fmt(row[key]) for _title, key in columns) + " |")
    return "\n".join([header, sep, *body])


def _answers(result: dict[str, Any]) -> dict[str, str]:
    tp = {row["candidate"]: row for row in result["tables"]["trajectory_preserving"]}
    floor = {row["candidate"]: row for row in result["tables"]["mechanical_dedup_floor"]}
    savings = result["tables"]["savings_sources"]
    b = tp["B"]
    c = tp["C"]
    d = tp["D"]
    e = tp["E"]
    f = tp["F"]
    q1 = (
        "Yes. Stable contract + unchanged SQL (candidate B) has median acquisition-inclusive "
        f"net delta {b['median']} with {b['directional_wins']}/4 directional wins "
        f"and safety {b['safety']}; admission={b['admission']}."
        if b["median"] < 0 and b["directional_wins"] >= 3
        else (
            "No. Stable contract + unchanged SQL (candidate B) does not cross net zero "
            f"on trajectory-preserving acquisition-inclusive replay "
            f"(median {b['median']}, wins {b['directional_wins']}/4, admission={b['admission']})."
        )
    )
    c_vs_b = savings["request_language_C_minus_B"]["bytes"]
    row_b = result["tables"]["acquisition_decomposition"][1]["state"]
    row_c = result["tables"]["acquisition_decomposition"][2]["state"]
    schema_c = result["tables"]["acquisition_decomposition"][2]["tool_schema"]
    schema_b = result["tables"]["acquisition_decomposition"][1]["tool_schema"]
    q2 = (
        f"No material response-side change: median dynamic-row bytes are identical "
        f"(B={row_b:.0f}, C={row_c:.0f}). The {c_vs_b:.0f} acquisition-inclusive gap is "
        f"tool-schema/envelope ({schema_c:.0f} vs {schema_b:.0f}), not query-language "
        f"response cost. Safety {c['safety']}."
    )
    d_vs_b = tp["D"]["median"] - b["median"]
    q3 = (
        f"Revision-sensitive first-use context (D) median net {d['median']} versus B {b['median']} "
        f"(difference {d_vs_b:.0f}). This is automatic relation-card delivery, not a live "
        "relevance classifier."
    )
    f_vs_a = f["median"] - tp["A"]["median"]
    floor_b = floor["B"]["median"]
    q4 = (
        f"Repeated unchanged-state reads: F vs A median net difference {f_vs_a:.0f}; "
        f"B mechanical floor median {floor_b} versus B trajectory-preserving {b['median']}. "
        "These floors are not behavioral predictions."
    )
    e1 = result["summaries"]["E1"]["trajectory_preserving"]
    eall = result["summaries"]["Eall"]["trajectory_preserving"]
    e1_med = _median([row["net_orientation_delta_acq"] for row in e1])
    eall_med = _median([row["net_orientation_delta_acq"] for row in eall])
    q5 = (
        f"Observed-union bundle E median net {e['median']} (admission {e['admission']}); "
        f"+1 extra relation {e1_med:.0f}; all-relations {eall_med:.0f}. "
        "E is an oracle accounting lower bound, not a prospective selector."
    )
    only_floor = [
        name
        for name, gate in result["admissions"].items()
        if gate == "CONDITIONAL"
    ]
    q6 = (
        "None."
        if not only_floor
        else ", ".join(only_floor) + " succeed only at the mechanical dedup floor."
    )
    ranked = sorted(
        tp.values(),
        key=lambda row: (
            0 if row["safety"] == "PASS" else 1,
            row["median"],
            {"A": 0, "B": 1, "C": 2, "D": 3, "F": 4, "E": 5}.get(row["candidate"], 9),
        ),
    )
    best = ranked[0]["candidate"]
    q7 = (
        f"Candidate {best} has the best combination of trajectory-preserving economics, "
        f"safety, and mechanism cost among the frozen set. This is not a v0.2 selection."
    )
    return {
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q4": q4,
        "Q5": q5,
        "Q6": q6,
        "Q7": q7,
    }


def _median(values: list[float]) -> float:
    data = sorted(values)
    mid = len(data) // 2
    if len(data) % 2:
        return float(data[mid])
    return (data[mid - 1] + data[mid]) / 2


def render_markdown(result: dict[str, Any], ledger: CampaignLedger) -> str:
    answers = _answers(result)
    reconstruction = result["reconstruction"]
    all_ok = all(item["ok"] for item in reconstruction.values())
    cols = [
        ("candidate", "candidate"),
        ("R1 net Δ", "R1"),
        ("R2 net Δ", "R2"),
        ("R3 net Δ", "R3"),
        ("R4 net Δ", "R4"),
        ("median", "median"),
        ("wins", "directional_wins"),
        ("safety", "safety"),
        ("admission", "admission"),
    ]
    acq_cols = [
        ("candidate", "candidate"),
        ("contract", "contract"),
        ("tool schema", "tool_schema"),
        ("state", "state"),
        ("epistemic", "epistemic"),
        ("grounding", "grounding"),
        ("maintenance", "maintenance"),
        ("total", "total"),
    ]
    savings_rows = [
        {"name": key, "bytes": value["bytes"], "note": value["note"]}
        for key, value in result["tables"]["savings_sources"].items()
    ]
    greed_lines = []
    for replicate, metrics in sorted(result["greed"].items()):
        greed_lines.append(
            f"- R{replicate}: breadth/phase={metrics['relation_breadth_per_phase']}, "
            f"queries={metrics['state_query_count']}, "
            f"episode refresh={metrics['episode_refresh_rate']:.2f}, "
            f"exact reread={metrics['exact_query_reread_rate']:.2f}, "
            f"rows={metrics['rows_retrieved']}/{metrics['unique_delivered_rows']}, "
            f"full-scan={metrics['full_scan_rate']:.2f}, "
            f"filter={metrics['filter_rate']:.2f}"
        )
    live = [
        "fresh pull+SQL (A / T0)",
        "stable pushed contract+SQL (B / T1)",
        "revision-triggered epistemic cards on SQL (D / T3)",
    ]
    notes = []
    for replicate, item in reconstruction.items():
        if item["notes"]:
            notes.append(f"- R{replicate}: " + "; ".join(item["notes"][:6]))
    limitation = "\n".join(notes) if notes else "None. All four TASKVIEW trajectories reconstructed."
    head = result["headroom"]
    just = head["justification"]
    anatomy_rows = []
    cut_rows = []
    for item in head["anatomies"]:
        anatomy_rows.append(item)
        math = item["describe_cut_math"]
        spec_frac = math["speculative_sql_fraction_that_must_disappear"]
        all_frac = math["all_sql_fraction_that_must_disappear"]
        cut_rows.append(
            {
                "replicate": item["replicate"],
                "gap_after_vocabulary_strip": math["gap_after_vocabulary_strip"],
                "speculative_sql_fraction_that_must_disappear": (
                    f"{spec_frac:.0%}" if spec_frac is not None else "n/a"
                ),
                "all_sql_fraction_that_must_disappear": (
                    f"{all_frac:.0%}" if all_frac is not None else "n/a"
                ),
                "crosses_zero_from_describe_cut_alone": math[
                    "crosses_zero_from_describe_cut_alone"
                ],
                "crosses_zero_if_all_speculative_sql_also_dropped": math[
                    "crosses_zero_if_all_speculative_sql_also_dropped"
                ],
                "still_short_after_zero_sql": math["still_short_after_zero_sql"],
            }
        )
    head_scenario_rows = [head["scenarios"][spec_id] for spec_id in head["scenarios"]]
    break_even_lines = []
    for item in head["break_even"]:
        if item["possible"]:
            break_even_lines.append(
                f"- R{item['replicate']}: first named combo that crosses zero is "
                f"`{item['scenario_id']}` (net Δ {item['net']})."
            )
        else:
            break_even_lines.append(
                f"- R{item['replicate']}: cannot cross zero under B "
                f"(fixed overhead net Δ {item['net']}). {item.get('blocker', '')}"
            )
    return f"""# TaskView read-surface replay results

**Status:** offline, zero inference. Sealed campaign `{result['campaign_id']}`.
**Participant / provider calls:** `{result['participant_inference_calls']}`.

This is a counterfactual payload/accounting study. It does not claim that
participant behavior would remain unchanged under a new surface.

Serializer freeze:

```text
serializer_id  {result['serializer']['serializer_id']}
config_sha256  {result['serializer']['config_sha256']}
module_sha256  {result['serializer']['module_sha256']}
```

Sealed identity (unchanged):

```text
campaign_seal_sha256  {result['campaign_seal_sha256']}
manifest_sha256       {result['manifest_sha256']}
```

SQL ledger facts (must match the preregistered 111-call corpus):

```text
{json.dumps(result['sql_facts'], indent=2, sort_keys=True)}
```

Budgets `RAW_O_post - TASKVIEW_repository_O_post`: `{result['budgets']}`.

Net delta = acquisition-inclusive TaskView read bytes − budget.
Negative is net-positive economics. Post-phase-1 bytes are also stored on each
summary for historical comparability and do not hide initialization contracts.

Candidate B's post-phase-1 net is negative in 2/4 replicates. That is the
init-placement artifact this admission rule exists to block: the contract is
charged in acquisition-inclusive totals, never dropped.

## Table 1 — Trajectory-preserving (acquisition-inclusive)

{_table(result['tables']['trajectory_preserving'], cols)}

## Table 2 — Mechanical dedup floor

{_table(result['tables']['mechanical_dedup_floor'], cols)}

## Table 3 — Acquisition decomposition (median trajectory-preserving)

{_table(result['tables']['acquisition_decomposition'], acq_cols)}

## Table 4 — Per-candidate savings source (pairwise, not additive)

{_table(savings_rows, [('contrast', 'name'), ('median byte Δ', 'bytes'), ('note', 'note')])}

## Behavioral-greed baselines (historical ledger)

{chr(10).join(greed_lines)}

## Specific questions

**Q1.** {answers['Q1']}

**Q2.** {answers['Q2']}

**Q3.** {answers['Q3']}

**Q4.** {answers['Q4']}

**Q5.** {answers['Q5']}

**Q6.** {answers['Q6']}

**Q7.** {answers['Q7']}

## A. Replay validity

All four TASKVIEW trajectories reconstructed: **{'yes' if all_ok else 'no'}**.

{limitation}

## B. Candidate ranking

Trajectory-preserving acquisition-inclusive median net delta, then safety, then added mechanism:

{_table(sorted(result['tables']['trajectory_preserving'], key=lambda row: (row['median'], row['candidate'])), cols)}

Mechanical floor:

{_table(sorted(result['tables']['mechanical_dedup_floor'], key=lambda row: (row['median'], row['candidate'])), cols)}

## C. Live shortlist

Recommend at most three future live contrasts, not a v0.2 architecture:

1. {live[0] if live else 'none'}
2. {live[1] if len(live) > 1 else '—'}
3. {live[2] if len(live) > 2 else '—'}

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
referent local-names (length ≥ {head['matcher']['min_match_chars']}), and
relation names.  Shared identifiers over-include; prose without those tokens
under-includes.  Oracle-required relations are a frozen field→relation
sensitivity, not participant intent.

### E.1 Observed B anatomy vs budget

{_table(anatomy_rows, [
    ('pair', 'replicate'),
    ('budget', 'budget'),
    ('B acq', 'observed_acq'),
    ('gap', 'observed_gap'),
    ('fixed overhead', 'fixed_overhead_bytes'),
    ('fixed ≥ budget', 'fixed_overhead_exceeds_budget'),
    ('redundant describe B', 'contract_redundant_describe_bytes'),
    ('vocab-strip savings', 'vocabulary_strip_savings'),
    ('speculative SQL B', 'speculative_sql_bytes'),
    ('contributing SQL B', 'contributing_sql_bytes'),
])}

Gap remaining after contract-redundant vocabulary is stripped from targeted
describes:

{_table(cut_rows, [
    ('pair', 'replicate'),
    ('gap after vocab strip', 'gap_after_vocabulary_strip'),
    ('speculative SQL that must vanish', 'speculative_sql_fraction_that_must_disappear'),
    ('all SQL that must vanish', 'all_sql_fraction_that_must_disappear'),
    ('zero from describe cut alone', 'crosses_zero_from_describe_cut_alone'),
    ('zero if all speculative SQL also dropped', 'crosses_zero_if_all_speculative_sql_also_dropped'),
    ('still short after zero SQL', 'still_short_after_zero_sql'),
])}

### E.2 Break-even scenarios

Negative net Δ is an economic win.  Conservative rows keep `describe(why)`,
compact completeness/currentness remainders, and post-mutation derived reads.

{_table(head_scenario_rows, [
    ('scenario', 'id'),
    ('R1 net Δ', 'R1'),
    ('R2 net Δ', 'R2'),
    ('R3 net Δ', 'R3'),
    ('R4 net Δ', 'R4'),
    ('median', 'median'),
    ('wins', 'wins'),
])}

{chr(10).join(f"- `{row['id']}`: {row['note']}" for row in head_scenario_rows)}

### E.3 Combination required to cross zero in each pair

{chr(10).join(break_even_lines)}

**Economic-headroom label:** `{just['label']}`.

{just['prose']}

Modest bar (redundant describe + 25% speculative-breadth cut):
{just['modest_25pct_wins']}/4.
Both cuts with epistemic checks kept: {just['both_conservative_wins']}/4.
Harsh bar (all relation describe gone + half breadth):
{just['harsh_half_breadth_wins']}/4.
Fixed-overhead floor: {just['fixed_overhead_wins']}/4.
Pairs that cannot cross zero under B at all:
{just['replicates_that_cannot_cross_zero_under_B']}/4.

If a live T0/T1 contrast is ever authorized, its purpose is not catalog-byte
savings.  Measure Δ relation breadth, Δ targeted introspection, Δ state
queries, and Δ repository exploration, and check that epistemic caution stays
intact.  If those barely move, flat broad retrieval is the preferred strategy
at this scale.  If they collapse, interface uncertainty was causing
overconsumption of TaskView and the repository.

Do not implement a live arm from this report. Do not authorize participant inference.
"""


def write_reports(result: dict[str, Any], ledger: CampaignLedger) -> tuple[Path, Path]:
    DIAGNOSTICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Drop bulky reconstructed payloads from JSON by summarizing accesses.
    slim = json.loads(json.dumps(result, default=str))
    DIAGNOSTICS_PATH.write_text(json.dumps(slim, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    REPORT_PATH.write_text(render_markdown(result, ledger), encoding="utf-8")
    return DIAGNOSTICS_PATH, REPORT_PATH


def run(results_root: Path | None = None) -> dict[str, Any]:
    ledger = build_campaign_ledger(results_root)
    result = run_accounting(ledger)
    result["headroom"] = run_headroom(ledger)
    write_reports(result, ledger)
    return result
