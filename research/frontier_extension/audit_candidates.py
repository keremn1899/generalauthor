"""Render a review audit for non-experimental frontier candidate worlds.

This consumes already-generated candidate artifacts and does not create a
participant workspace, issue a model call, or change a candidate artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FAMILIES = {
    "Depth / closure": ["FX01", "FX02", "FX03"],
    "Intermediate reuse": ["FX14", "FX06", "FX07"],
    "Cyclic topology": ["FX08", "FX09"],
    "Negative / absence": ["FX10", "FX11"],
}
PROBES = {
    "FX04": "constrained reachability",
    "FX05": "ordered relation sequence",
    "FX12": "qualified branching / set composition",
    "FX13": "constrained multi-output topology",
}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell(value: Any) -> str:
    return str(value).replace("|", "\\|")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=ROOT / "research/frontier_extension/candidates_v2")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    base = args.candidates.resolve()
    output = (args.out or base / "GENERATED_WORLD_REVIEW_AUDIT.md").resolve()
    rows: list[dict[str, Any]] = []
    for case_dir in sorted((base / "cases").iterdir()):
        meta, admission, oracle = (load(case_dir / name) for name in ("metadata.json", "admission.json", "oracle.json"))
        rows.append({
            "case": meta["case"], "meta": meta, "admission": admission, "oracle": oracle,
            "canonical_hash": sha256(case_dir / "canonical_facts.json"),
            "oracle_hash": sha256(case_dir / "oracle.json"),
            "graph_hash": sha256(case_dir / "t_graph.lbug"),
            "sql_hash": sha256(case_dir / "t_sql.sqlite"),
        })
    by_case = {row["case"]: row for row in rows}
    missing = (set().union(*[set(cases) for cases in FAMILIES.values()], set(PROBES)) - set(by_case))
    if missing:
        raise SystemExit(f"candidate cases missing from audit: {sorted(missing)}")
    admitted = all(
        row["admission"]["passed"]
        and row["admission"]["sql_parity"]
        and row["admission"]["graph_parity"]
        and row["admission"]["oracle_exact"]
        for row in rows
    )
    family_lines = []
    for family, cases in FAMILIES.items():
        values = [by_case[case]["meta"] for case in cases]
        family_lines.append(
            f"| {family} | {' → '.join(cases)} | "
            f"{' → '.join(str(v['required_depth']) for v in values)} | "
            f"{' → '.join(str(v['oracle_relevant_closure_size']) for v in values)} |"
        )
    case_lines = []
    for row in rows:
        meta, admission, oracle = row["meta"], row["admission"], row["oracle"]
        checks = admission["graph"]
        all_graph_checks = all(checks.values())
        case_lines.append(
            "| {case} | {platform} | {depth} | {closure} | {cycle} | {absence} | {outputs} | {answers} | "
            "{oracle} | {sql_parity} | {graph_parity} | {feasible} |".format(
                case=meta["case"], platform=meta["platform"], depth=meta["required_depth"],
                closure=meta["oracle_relevant_closure_size"], cycle=meta["cycle"],
                absence=meta["absence_proof"], outputs=meta["named_output_count"],
                answers=meta["answer_size"], oracle=admission["oracle_exact"],
                sql_parity=admission["sql_parity"], graph_parity=admission["graph_parity"],
                feasible=all_graph_checks and admission["sql"]["recursive_cte"],
            )
        )
    hash_lines = []
    for row in rows:
        hash_lines.append(
            f"| {row['case']} | `{row['canonical_hash']}` | `{row['oracle_hash']}` | "
            f"`{row['sql_hash']}` | `{row['graph_hash']}` |"
        )
    prompt_lines = []
    for row in rows:
        meta = row["meta"]
        prompt_lines.append(f"### {meta['case']} — {meta['template']}\n\n{cell(meta['prompt'])}\n\nNeutral oracle: `{json.dumps(meta['neutral_program'], sort_keys=True)}`.\n")
    status = "PASS" if admitted else "FAIL"
    report = f"""# Generated-world review audit — frontier extension

## Result

**{status}: 14/14 candidate worlds admitted mechanically.** No participant
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
| Candidate directory | `{base.relative_to(ROOT)}` |
| Graph treatment fingerprint | `{rows[0]['admission']['treatment_fingerprint']}` |
| SQLite version admitted | `{rows[0]['admission']['sql']['sqlite_version']}` |
| Participants run | `false` |

## Preregistered dose-response families

| Family | Cases | Required depth | Oracle-relevant closure |
| --- | --- | --- | --- |
{chr(10).join(family_lines)}

Mechanism probes, reported separately after execution: FX04 constrained
reachability; FX05 ordered relation sequence; FX12 qualified branching/set
composition; FX13 constrained multi-output topology.

## Mechanical-admission summary

| Case | Platform | Depth | Closure | Cycle | Absence | Named outputs | Answer IDs | Oracle | SQL parity | Graph parity | Feasible |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- | --- | --- | --- |
{chr(10).join(case_lines)}

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
{chr(10).join(hash_lines)}

## Prompt and neutral-oracle review inputs

{chr(10).join(prompt_lines)}

## Required human decision before participant execution

Approve or reject these candidate worlds as a batch after reviewing their
prompts, canonical facts, and oracle artifacts. On approval, freeze the
candidate hashes, adapter hash, product commit, Python environment, and case/
arm ordering in a campaign manifest. Do not replace individual cases after any
participant outcome.
"""
    output.write_text(report, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
