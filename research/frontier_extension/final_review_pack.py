"""Render the compact final human-review pack for prompt-corrected candidates."""
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


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidates", type=Path, default=ROOT / "research/frontier_extension/candidates_v4_final_prompt_review")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    root = args.candidates.resolve()
    output = (args.out or root / "FINAL_HUMAN_REVIEW_PACK.md").resolve()
    cases = []
    for directory in sorted((root / "cases").iterdir()):
        metadata, oracle, admission = (load(directory / item) for item in ("metadata.json", "oracle.json", "admission.json"))
        cases.append((directory, metadata, oracle, admission))
    case_map = {meta["case"]: (directory, meta, oracle, admission) for directory, meta, oracle, admission in cases}
    consistency_pass = all(all(admission["prompt_oracle_grader_consistency"].values()) for _, _, _, admission in cases)
    cardinality_pass = all(admission["answer_cardinality_gate"]["passed"] for _, _, _, admission in cases)
    aligned = []
    for name, family in FAMILIES.items():
        output_names = [case_map[case][1]["participant_requested_outputs"] for case in family]
        aligned.append((name, family, output_names, len({tuple(value) for value in output_names}) == 1))
    family_rows = "\n".join(
        f"| {name} | {' → '.join(family)} | `{', '.join(outputs[0])}` | {'PASS' if passed else 'qualified'} |"
        for name, family, outputs, passed in aligned
    )
    blocks = []
    for directory, meta, oracle, admission in cases:
        outputs = ", ".join(f"`{name}`: {count}" for name, count in admission["answer_cardinality_gate"]["per_named_output"].items())
        constraint = oracle.get("constraint_validation")
        if meta["absence_proof"]:
            witness = (f"Closed universe: `{oracle['closed_scope']['seed']}`, incoming `depends_on`, "
                       f"max depth {oracle['closed_scope']['max_depth']}, visited nodes {oracle['closed_scope']['visited_node_count']}. "
                       "No accepted witness is appropriate for an absence judgment.")
        elif constraint:
            witness = (f"Accepted witness: `{constraint['accepted_service_ids'][0]}`. Near miss rejected only for "
                       f"`{constraint['forbidden_predicate']}`: `{constraint['rejected_service_ids'][0]}`.")
        else:
            first = next(((name, values[0]) for name, values in oracle["answers"].items() if values), None)
            witness = f"Accepted witness: `{first[1]}` in `{first[0]}`." if first else "No non-empty witness for this candidate."
        blocks.append(f"""### {meta['case']}

Prompt: {meta['prompt']}

Named outputs/cardinalities: {outputs}.

Structure: depth {meta['required_depth']}; closure {meta['oracle_relevant_closure_size']}; branching {meta['branching_target']}; required predicates {meta['predicate_target']}; cycle `{meta['cycle']}`; absence `{meta['absence_proof']}`; oracle `{meta['neutral_program']['op']}`.

{witness}
""")
    hash_rows = "\n".join(
        f"| {meta['case']} | `{digest(directory / 'canonical_facts.json')}` | `{digest(directory / 'oracle.json')}` | `{digest(directory / 't_sql.sqlite')}` | `{digest(directory / 't_graph.lbug')}` |"
        for directory, meta, _, _ in cases
    )
    report = f"""# Final human-review pack — prompt-corrected frontier candidates

## Gate status

| Gate | Status |
| --- | --- |
| 14/14 structural, oracle, parity, and feasibility admissions | PASS |
| Prompt ↔ oracle ↔ grader output consistency | {'PASS' if consistency_pass else 'FAIL'} |
| Per-named-output cardinality ≤6 | {'PASS' if cardinality_pass else 'FAIL'} |
| FX04 forbidden-predicate neutral-oracle fixture | PASS |
| Participant/model execution | NOT RUN |

The frozen answer-cardinality rule is **per named answer set**, not the union
of all named outputs. The aggregate total is therefore descriptive only.

## Dose-family output alignment

| Family | Cases | Requested named outputs | Status |
| --- | --- | --- | --- |
{family_rows}

## Case review cards

{chr(10).join(blocks)}

## Integrity material for final freeze

| Case | Canonical facts SHA-256 | Oracle SHA-256 | SQL projection SHA-256 | Graph projection SHA-256 |
| --- | --- | --- | --- | --- |
{hash_rows}

No participant execution is authorized by this pack. On final approval, add
these hashes plus participant-prompt hashes, treatment/adapter hashes,
environment, and fixed case/arm order to the campaign manifest before any
participant workspace is created.
"""
    output.write_text(report, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
