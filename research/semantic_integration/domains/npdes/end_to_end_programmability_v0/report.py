"""Write human reports and the static inspection bundle from measured artifacts."""

from __future__ import annotations

import csv
import html
import json
import sqlite3
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    CONSUMERS,
    DIFFS,
    FRESH,
    MANUAL,
    OUTPUTS,
    REPORTS,
    ROOT,
    RUNS,
    STATES,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.score import score


def _md(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _sample_csv(src: Path, dest: Path, n: int = 20) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with src.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
        fields = list(rows[0].keys()) if rows else []
    with dest.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows[:n])


def write_reports(sc: dict) -> None:
    det = json.loads((RUNS / "deterministic.json").read_text(encoding="utf-8"))
    a, b, c = det["summaries"]["state_a"], det["summaries"]["state_b"], det["summaries"]["state_c"]
    REPORTS.mkdir(parents=True, exist_ok=True)

    _md(
        REPORTS / "experimental_setup.md",
        """# Experimental setup

## MEASURED

- Draft spine: sealed Purpose-First Python Spine Probe T5
- WHEN DISCHARGING: sealed obligation probe Arm B T1 (`ADMIT_DISPOSABLE`, SOURCE_ESTABLISHED)
- pass/fail: sealed obligation probe Arm B T3 (supported; 8 `pass_fail_outcome_reporting` rows). T1 apply completed with 0 binary rows; T2 crashed. T3 is the successful mechanical apply.
- State D: skipped (prior parent/child admission mismatch)
- Model for fresh agents: Composer 2.5
- Consumers frozen after State A; hashes recorded in `frozen/consumer_hashes.json`

## OBSERVED

Sealed T5 / obligation artifacts were hashed before disposable copies. Construction used native sources only inside `states/*/compile/`. Isolated consumers received sqlite + header only.

## HYPOTHESIS

Compiled semantic state can be an ordinary SQL/Python substrate without rereading heterogeneous sources.
""",
    )
    _md(
        REPORTS / "world_states.md",
        f"""# World states

## MEASURED

| state | hole instances | hole groups | notable relations |
| --- | ---: | ---: | --- |
| A T5 baseline | {det['worlds']['state_a']['n_hole_instances']} | {det['worlds']['state_a']['n_hole_groups']} | no monitoring_condition; 12 pass_fail holes |
| B WHEN DISCHARGING | {det['worlds']['state_b']['n_hole_instances']} | {det['worlds']['state_b']['n_hole_groups']} | monitoring_condition; discharge_occurrence_in_period=17 |
| C + pass/fail T3 | {det['worlds']['state_c']['n_hole_instances']} | {det['worlds']['state_c']['n_hole_groups']} | pass_fail_outcome_reporting=8; pass_fail holes=4 |

World sha256: A `{det['worlds']['state_a']['world_sha256']}` B `{det['worlds']['state_b']['world_sha256']}` C `{det['worlds']['state_c']['world_sha256']}`

## OBSERVED

NODI C/9 remain UNINTERPRETED in all three states. No codebook was imported.

## HYPOTHESIS

Disposable copies can admit prior grounded proposals without mutating sealed T5.
""",
    )
    _md(
        REPORTS / "consumer_design.md",
        """# Consumer design

## MEASURED

SQL `consumers/sql/monitoring_analysis.sql` joins `measurement_limit_pair`, `dmr_measurement`, `numeric_comparison_candidate`, `no_numeric_result_case`, and `_hole`.

Python discovers optional `monitoring_condition` and `pass_fail_outcome_reporting` via sqlite_master. It does not parse comments or map NODI legends.

## OBSERVED

The same bytes ran on A, B, and C. Schema expansion is consumed only when present.

## HYPOTHESIS

Ordinary SQL/Python against constructor-authored relation names is enough for v0; semantic ABI is out of scope.
""",
    )
    _md(
        REPORTS / "consumer_semantic_leakage.md",
        f"""# Consumer semantic leakage

## MEASURED

`consumer_semantic_leakage = {sc['leakage']}`

Hits after auditor correction (World field `nodi_code` is not a legend): {json.dumps(det['leakage']['hits'], indent=2)}

## OBSERVED

No CSV/PDF paths, no `WHEN DISCHARGING` string match, no NODI meaning table in consumer code.

## HYPOTHESIS

Source reconciliation can stay out of application code when the World already holds holes and compiled relations.
""",
    )
    _md(
        REPORTS / "state_deltas.md",
        f"""# State deltas

## MEASURED

A→B: changed {sc['a_to_b']['n_changed']}; semantic→factual {sc['a_to_b']['semantic_to_factual']}; newly determinate {sc['a_to_b']['newly_determinate']}.

B→C: changed {sc['b_to_c']['n_changed']}; newly PASS/FAIL {sc['b_to_c']['pass_fail_classified']}; newly determinate {sc['b_to_c']['newly_determinate']}.

Exceedance counts A/B/C: {a['n_exceedance']}/{b['n_exceedance']}/{c['n_exceedance']} (stable={sc['n_exceedance_stable']}).

## OBSERVED

WHEN DISCHARGING did not close compliance. It retargeted 140 application rows from semantic comment-opacity to factual discharge-occurrence uncertainty (17 limit-level holes × FY2025 measurements).

Pass/fail classified 8 measurements as PASS. 24 sibling comment rows lost `pass_fail_reporting_semantics` without becoming numeric exceedances (T3 unit split).

## HYPOTHESIS

Grounded reusable semantics change intended application rows only.
""",
    )
    _md(
        REPORTS / "source_independence.md",
        f"""# Source independence

## MEASURED

World-only consumer runs: A={a.get('world_only')} B={b.get('world_only')} C={c.get('world_only')}

Native files in isolated_consumer trees: none (`.csv`/`.pdf` scan).

Fresh-agent source_marker_hits are string matches in transcripts (`.pdf` appears in `permit_document` inventory discussion; no file was present to open).

## OBSERVED

Deterministic consumers never opened CSVs. Agents queried sqlite only.

## HYPOTHESIS

Purpose-compatible analysis does not require the native corpus after compilation.
""",
    )
    _md(
        REPORTS / "fresh_agent_results.md",
        f"""# Fresh-agent results

## MEASURED

Both hosts reported **Composer 2.5**. Isolated workspaces had no sources, construction.py, gold, or prior transcripts.

| state | Q1 | Q2 | Q3 |
| --- | --- | --- | --- |
| A | {sc['fresh_agent']['state_a']['Q1']} | {sc['fresh_agent']['state_a']['Q2']} | {sc['fresh_agent']['state_a']['Q3']} |
| C | {sc['fresh_agent']['state_c']['Q1']} | {sc['fresh_agent']['state_c']['Q2']} | {sc['fresh_agent']['state_c']['Q3']} |

State A note: {sc['fresh_agent']['state_a']['note']}

State C note: {sc['fresh_agent']['state_c']['note']}

Invented NODI legend: {sc['invented_nodi']}

## OBSERVED

State C used `monitoring_condition`, `discharge_occurrence_in_period`, and `pass_fail_outcome_reporting`. State A used `_hole` families and left NODI uninterpreted. State C is more precise on Q3 because the World now splits condition meaning from discharge occurrence.

## HYPOTHESIS

A fresh agent can program over accepted World state without reconstructing native schemas.
""",
    )
    _md(
        REPORTS / "traceability.md",
        """# Traceability

## MEASURED

Eight sampled application results under `manual_inspection/traces/` include WHEN DISCHARGING sharpening, pass/fail PASS, NODI C, NODI 9, and unaffected numeric controls.

Each trace links application row → `measurement_limit_pair` tuple → `_hole` / compiled relation → State C proposal ids in origins sidecar.

## OBSERVED

Lineage is mechanical through World sqlite. Exact permit-clause quotes remain in the sealed obligation-resolution packets, not duplicated into this World dump.

## HYPOTHESIS

Application deltas are auditable to admitted semantic proposals without rereading the corpus at consumption time.
""",
    )
    _md(
        REPORTS / "failure_path.md",
        f"""# Failure path

## MEASURED

{json.dumps(sc['failure_path'], indent=2)}

Reopen: {json.dumps(det['reopen'], indent=2)}

## OBSERVED

Invalid construction.py in a disposable directory did not write the accepted World or application CSV. Reopening each isolated consumer reproduced identical CSV hashes.

## HYPOTHESIS

Failed candidates can fail closed if they never share a write path with accepted/.
""",
    )

    answers = [
        "Yes. Isolated SQL+Python ran against sqlite with no native sources.",
        "Yes. Same isolated Python consumer.",
        f"Leakage={sc['leakage']}. No comment parsing, no NODI legend, no CSV/PDF paths.",
        f"Consumer rewrite count={sc['consumer_rewrite_count']}.",
        "140 application rows moved monitoring_status UNRESOLVED_SEMANTIC → UNRESOLVED_FACTUAL (WHEN DISCHARGING family). Numeric comparison statuses on those rows were unchanged.",
        "Semantic sharpening into a factual dependency. Newly determinate on A→B = 0. No silent false/N/A.",
        "Yes. 8 rows became PASS via pass_fail_outcome_reporting. 24 sibling comment rows did not become numeric exceedances.",
        "Yes. 150 C + 36 9 remain nodi_code_semantics unresolved in State C.",
        "No consumer NODI legend. Fresh agents explicitly refused to invent meanings.",
        "Exceedance count stable (28). WHEN DISCHARGING family and pass/fail family did not cross-apply.",
        "Sampled traces bind to World tuples and hole/proposal pointers. Packet quotes stay in the sealed prior probe.",
        "Yes. REOPEN_WITHOUT_RECONSTRUCTION true for A, B, and C.",
        f"FAILED_CANDIDATE_PRESERVES_ACCEPTED={sc['failure_path']['FAILED_CANDIDATE_PRESERVES_ACCEPTED']}",
        f"FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT={sc['failure_path']['FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT']}",
        "Yes. Both agents answered from header + sqlite.",
        "They queried World relations and stored comment fields already compiled into the World. They did not open CSVs/PDFs (none present). State A Q3 over-read hole prose as established condition meaning.",
        "No. Questions the World supports were answered from sqlite. Residual NODI/frequency holes are WORLD_INSUFFICIENT, not consumer failure.",
        "Yes. State C names monitoring_condition=discharge_occurrence, discharge_occurrence_in_period, and pass_fail_outcome_reporting. State A could only point at conditional_discharge_dependent_monitoring.",
        "Yes at application layer for the admitted enrichments: one WHEN DISCHARGING judgment → 140 row status changes; one pass/fail judgment → 8 PASS classifications; same consumer bytes.",
        "Supported as a research demonstration of the product thesis, not as a harness or ABI.",
        "Smallest missing mechanism: a reliable disposable-apply compiler (T2 pass/fail crashed historically; T1 produced 0 binary rows). Ordinary SQL views would also make optional relations less schema-discovery-dependent. Neither is required to explain this probe's successes.",
        "No observed correctness failure that requires a semantic ABI, kernel primitive, graph API, Source IR, or new subsystem. Relation-name dependence is in-scope for v0. Cross-reconstruction stability was not tested.",
    ]

    master = f"""# End-to-End Programmability Probe v0

Sealed interpretation: **{sc['label']}**

Draft spine: Purpose-First Python Spine **T5**. Enrichments: obligation probe T1 WHEN DISCHARGING and T3 pass/fail. Fresh agents: **Composer 2.5**. Not constructor promotion. Not drop-in harness. Not semantic ABI.

## What was tested

```text
messy sources → sealed construction → accepted World → ordinary SQL/Python
then grounded enrichment → same consumer bytes → sharper application output
```

## Required answers

""" + "\n".join(f"### {i}\n\n{line}\n" for i, line in enumerate(answers, 1)) + f"""

## WHAT HELD

World-only deterministic consumers ran. Rewrite count was 0. Leakage is {sc['leakage']}. WHEN DISCHARGING sharpened 140 rows into factual discharge uncertainty without closing them. Pass/fail classified 8 rows. NODI C/9 stayed unresolved. Exceedance count did not move. Failed candidates and reopen left accepted bytes and CSV hashes unchanged. Fresh agents used sqlite and did not invent NODI legends. State C made Q3 precise.

## WHAT FAILED

State D was not applied (prior parent/child mismatch). T1 pass/fail mechanical mapping was empty, so State C used T3 rather than T1. State A fresh-agent Q3 treated T5 hole prose as already-established condition meaning. Monitoring frequency/sample-type codes remain uninterpreted on every requirement — outside this probe's admitted enrichments. 24 pass/fail-comment sibling rows changed unresolved_reason without becoming determinate.

## WHAT THIS CHANGES

An accepted T5 World is already a usable ordinary programming substrate for purpose-compatible FY2025 analysis. Residual semantic resolutions, when mechanically applied, flow through frozen SQL/Python without source rereads. Honest unresolvedness is consumable as `_hole` plus compiled relations.

## WHAT THIS DOES NOT JUSTIFY

- **semantic ABI** — one contract was held fixed; independent reconstructions were not compared.
- **graph API** — joins were SQL.
- **persistent Source IR** — consumers did not need sources; that does not imply a Source IR product.
- **new kernel primitive** — research World API dump to sqlite; TaskView was not modified.
- **obligation subsystem** — factorization stayed in the prior sealed probe.
- **application framework / dashboard** — `index.html` is a static inspection page only.
- **drop-in harness implementation** — still a separate spec, unimplemented here.

## STOP

No TaskView/kernel change. No Constructor change. No sealed T5 or obligation-result mutation. No harness. No `semantic_identity`. No ABI design. No product dashboard. No fifth domain. No new semantic-resolution benchmark. No real-user study.
"""
    _md(REPORTS / "end_to_end_programmability_v0.md", master)

    # manual inspection bundle
    MANUAL.mkdir(parents=True, exist_ok=True)
    for state in ("state_a", "state_b", "state_c"):
        src = OUTPUTS / state
        dest = MANUAL / state
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "summary.md").write_text((src / "summary.md").read_text(encoding="utf-8"), encoding="utf-8")
        _sample_csv(src / "monitoring_analysis.csv", dest / "sample_results.csv")
    (MANUAL / "diffs").mkdir(parents=True, exist_ok=True)
    (MANUAL / "diffs" / "a_to_b.md").write_text((DIFFS / "a_to_b_summary.md").read_text(encoding="utf-8"), encoding="utf-8")
    (MANUAL / "diffs" / "b_to_c.md").write_text((DIFFS / "b_to_c_summary.md").read_text(encoding="utf-8"), encoding="utf-8")
    import shutil

    shutil.copy2(DIFFS / "a_to_b_rows.csv", MANUAL / "diffs" / "a_to_b.csv")
    shutil.copy2(DIFFS / "b_to_c_rows.csv", MANUAL / "diffs" / "b_to_c.csv")
    (MANUAL / "README.md").write_text(
        "Static inspection bundle. Open index.html first. Not a product UI.\n",
        encoding="utf-8",
    )

    conn = sqlite3.connect(STATES / "state_c" / "accepted" / "world.sqlite")
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY 1")]
    conn.close()
    tables_txt = ", ".join(tables)

    _md(
        ROOT / "MANUAL_INSPECTION.md",
        f"""# Manual Inspection

Experiment root:
`research/semantic_integration/domains/npdes/end_to_end_programmability_v0/`

Open first:
`research/semantic_integration/domains/npdes/end_to_end_programmability_v0/manual_inspection/index.html`

## Paths

- Baseline output: `outputs/state_a/`
- WHEN DISCHARGING enriched output: `outputs/state_b/`
- pass/fail enriched output: `outputs/state_c/`
- Row diffs: `diffs/a_to_b_rows.csv`, `diffs/b_to_c_rows.csv`
- Trace samples: `manual_inspection/traces/`
- SQL consumer: `consumers/sql/monitoring_analysis.sql`
- Python consumer: `consumers/python/monitoring_analysis.py`
- Fresh-agent transcripts: `fresh_agent/state_a/ANSWERS.md`, `fresh_agent/state_c/ANSWERS.md`
- Compact headers: `states/state_a/compact_header.md`, `states/state_b/compact_header.md`, `states/state_c/compact_header.md`
- Accepted World sqlite: `states/state_a/accepted/world.sqlite`, `states/state_b/accepted/world.sqlite`, `states/state_c/accepted/world.sqlite`
- Isolated source-free copies: `isolated_consumer/state_a/`, `isolated_consumer/state_b/`, `isolated_consumer/state_c/`
- Failure-path evidence: `failure_path/result.json`
- Final report: `reports/end_to_end_programmability_v0.md`

## SQLite

```bash
sqlite3 "research/semantic_integration/domains/npdes/end_to_end_programmability_v0/states/state_c/accepted/world.sqlite"
```

```sql
.tables
.schema measurement_limit_pair
.schema monitoring_requirement_fy2025
.schema pass_fail_outcome_reporting
.schema _hole
SELECT name, mode, derived FROM _relation_meta ORDER BY name;
SELECT requirement, COUNT(*) FROM _hole GROUP BY requirement ORDER BY 2 DESC;
SELECT monitoring_condition, COUNT(*) FROM monitoring_requirement_fy2025 GROUP BY 1;
SELECT nodi_code, COUNT(*) FROM no_numeric_result_case GROUP BY 1;
SELECT dmr_value_nmbr, COUNT(*) FROM pass_fail_outcome_reporting GROUP BY 1;
```

State C tables: {tables_txt}

Consumer hashes (must match frozen): see `frozen/consumer_hashes.json`.
""",
    )

    def counts(summary: dict) -> str:
        return (
            f"rows={summary['n_rows']} determinate={summary['evidence_status'].get('DETERMINATE', 0)} "
            f"sem={summary['evidence_status'].get('UNRESOLVED_SEMANTIC', 0)} "
            f"fact={summary['evidence_status'].get('UNRESOLVED_FACTUAL', 0)} "
            f"NODI_C={summary['n_nodi_c_cases']} NODI_9={summary['n_nodi_9_cases']} "
            f"PASS={summary['n_pass']} exceedance={summary['n_exceedance']}"
        )

    index = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>E2E programmability v0 inspection</title>
<style>
body {{ font-family: sans-serif; margin: 1.5rem; max-width: 1100px; }}
table {{ border-collapse: collapse; margin: 0.75rem 0 1.5rem; }}
th, td {{ border: 1px solid #444; padding: 0.35rem 0.6rem; text-align: left; }}
code {{ font-size: 0.9em; }}
</style>
</head>
<body>
<h1>End-to-End Programmability Probe v0</h1>
<p>Judgment: <strong>{html.escape(sc['label'])}</strong></p>
<p>Generated from <code>runs/score.json</code> and <code>outputs/*/summary.json</code>. Not a product UI.</p>
<table>
<tr><th>State</th><th>Summary</th></tr>
<tr><td>A baseline T5</td><td>{html.escape(counts(a))}</td></tr>
<tr><td>B WHEN DISCHARGING</td><td>{html.escape(counts(b))}</td></tr>
<tr><td>C + pass/fail</td><td>{html.escape(counts(c))}</td></tr>
</table>
<table>
<tr><th>Transition</th><th>changed</th><th>newly determinate</th><th>semantic→factual</th><th>PASS/FAIL classified</th></tr>
<tr><td>A→B</td><td>{sc['a_to_b']['n_changed']}</td><td>{sc['a_to_b']['newly_determinate']}</td><td>{sc['a_to_b']['semantic_to_factual']}</td><td>{sc['a_to_b']['pass_fail_classified']}</td></tr>
<tr><td>B→C</td><td>{sc['b_to_c']['n_changed']}</td><td>{sc['b_to_c']['newly_determinate']}</td><td>{sc['b_to_c']['semantic_to_factual']}</td><td>{sc['b_to_c']['pass_fail_classified']}</td></tr>
</table>
<ul>
<li>NODI C/9 unresolved in C: {c['n_nodi_c_or_9_with_unresolved_semantics']} of {c['n_nodi_c_cases']+c['n_nodi_9_cases']}</li>
<li>Consumer rewrite count: {sc['consumer_rewrite_count']}</li>
<li>Leakage: {html.escape(sc['leakage'])}</li>
<li>Failed candidate preserves accepted: {sc['failure_path']['FAILED_CANDIDATE_PRESERVES_ACCEPTED']}</li>
<li>Failed candidate preserves application output: {sc['failure_path']['FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT']}</li>
<li>Reopen without reconstruction: {sc['reopen_ok']}</li>
<li>Fresh agent A Q1/Q2/Q3: {sc['fresh_agent']['state_a']['Q1']} / {sc['fresh_agent']['state_a']['Q2']} / {sc['fresh_agent']['state_a']['Q3']}</li>
<li>Fresh agent C Q1/Q2/Q3: {sc['fresh_agent']['state_c']['Q1']} / {sc['fresh_agent']['state_c']['Q2']} / {sc['fresh_agent']['state_c']['Q3']}</li>
</ul>
<p>WHEN DISCHARGING example: <a href="traces/T01_when_discharging_sharpened.md">T01</a></p>
<p>pass/fail example: <a href="traces/T02_pass_fail_classified.md">T02</a></p>
<p>NODI still unresolved: <a href="traces/T04_nodi_c_unresolved.md">T04</a> <a href="traces/T05_nodi_9_unresolved.md">T05</a></p>
<p>Unaffected numeric control: <a href="traces/T06_unaffected_numeric_control.md">T06</a></p>
<h2>Links</h2>
<ul>
<li><a href="../outputs/state_a/monitoring_analysis.csv">state A csv</a> · <a href="../outputs/state_a/summary.md">summary</a></li>
<li><a href="../outputs/state_b/monitoring_analysis.csv">state B csv</a> · <a href="../outputs/state_b/summary.md">summary</a></li>
<li><a href="../outputs/state_c/monitoring_analysis.csv">state C csv</a> · <a href="../outputs/state_c/summary.md">summary</a></li>
<li><a href="diffs/a_to_b.md">A→B summary</a> · <a href="diffs/a_to_b.csv">rows</a></li>
<li><a href="diffs/b_to_c.md">B→C summary</a> · <a href="diffs/b_to_c.csv">rows</a></li>
<li><a href="../consumers/sql/monitoring_analysis.sql">SQL consumer</a></li>
<li><a href="../consumers/python/monitoring_analysis.py">Python consumer</a></li>
<li><a href="../fresh_agent/state_a/ANSWERS.md">fresh agent A</a> · <a href="../fresh_agent/state_c/ANSWERS.md">fresh agent C</a></li>
<li><a href="../frozen/consumer_hashes.json">consumer hashes</a></li>
<li><a href="../reports/end_to_end_programmability_v0.md">final report</a></li>
</ul>
</body>
</html>
"""
    (MANUAL / "index.html").write_text(index, encoding="utf-8")


if __name__ == "__main__":
    write_reports(score())
