"""Evaluate a frozen operational frontier against C0.  Load C0 only here."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from research.semantic_integration.harness import frontier, load_oracle_document
from research.taskview_bom.experiment import ORACLE_PATH, compile_c1, _relation_tuples


ROOT = Path(__file__).resolve().parent
FROZEN_PATH = ROOT / "operational_frontier.json"


def obligation_tuples(document: dict[str, Any]) -> set[tuple[Any, ...]]:
    tuples: set[tuple[Any, ...]] = set()
    for obligation in document["obligations"]:
        values = obligation["values"]
        tuples.add((values["new_part"], values["old_part"], values["context"]))
    return tuples


def oracle_residual(view) -> dict[str, set[tuple[Any, ...]]]:
    oracle = load_oracle_document(json.loads(ORACLE_PATH.read_text(encoding="utf-8")))
    compiled = {name: _relation_tuples(view, name) for name in oracle.tuples}
    return frontier(oracle, compiled)


def compare(operational: set[tuple[Any, ...]], expected: set[tuple[Any, ...]]) -> dict[str, Any]:
    true_positives = operational & expected
    false_positives = operational - expected
    false_negatives = expected - operational
    precision = (
        len(true_positives) / len(operational) if operational else 1.0
    )
    recall = len(true_positives) / len(expected) if expected else 1.0
    return {
        "true_positives": [list(row) for row in sorted(true_positives)],
        "false_positives": [list(row) for row in sorted(false_positives)],
        "false_negatives": [list(row) for row in sorted(false_negatives)],
        "true_positive_count": len(true_positives),
        "false_positive_count": len(false_positives),
        "false_negative_count": len(false_negatives),
        "precision": precision,
        "recall": recall,
        "exact_frontier_match": operational == expected,
    }


def evaluate(frozen_path: Path = FROZEN_PATH) -> dict[str, Any]:
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="operational-frontier-eval-") as temporary:
        compilation = compile_c1(Path(temporary) / "c1.sqlite")
        try:
            residual = oracle_residual(compilation.view)
            expected = residual.get("acceptable_replacement", set())
            comparison = compare(obligation_tuples(frozen), expected)
            return {
                "frozen_fingerprint": frozen.get("fingerprint"),
                "c1_world_revision": frozen["c1_world_revision"],
                "oracle_residual": {
                    name: [list(row) for row in sorted(rows)]
                    for name, rows in sorted(residual.items())
                },
                "comparison": comparison,
                "provider_inference_calls": 0,
            }
        finally:
            compilation.view.close()


def render_report(frozen: dict[str, Any], evaluation: dict[str, Any]) -> str:
    comparison = evaluation["comparison"]
    residual = evaluation["oracle_residual"]
    obligations = frozen["obligations"]
    obligation_lines = []
    for item in obligations:
        values = item["values"]
        obligation_lines.append(
            f"- `{item['relation']}({values['new_part']}, {values['old_part']}, "
            f"{values['context']})` demanded by purpose "
            f"`{item['demanded_by']['name']}` revision {item['demanded_by']['revision']}"
        )
    precision = comparison["precision"]
    recall = comparison["recall"]
    precision_display = (
        f"{comparison['true_positive_count']}/{frozen['obligation_count']}"
        if frozen["obligation_count"]
        else str(precision)
    )
    residual_count = sum(len(rows) for rows in residual.values())
    recall_display = (
        f"{comparison['true_positive_count']}/{residual_count}"
        if residual_count
        else str(recall)
    )
    residual_lines = []
    for relation, rows in residual.items():
        for row in rows:
            residual_lines.append(
                f"- `{relation}({', '.join(str(item) for item in row)})`"
            )
    return f"""# Oracle-free operational frontier (BOM S1)

Frozen before C0 evaluation. Provider/model inference calls: **0**.

## Frozen operational frontier

- Purpose: `{frozen["purpose"]["id"]}` revision {frozen["purpose"]["revision"]}
- Statement: {frozen["purpose"]["statement"]}
- Generation rule: `{frozen["generation_rule_version"]}`
- C1 world revision: {frozen["c1_world_revision"]}
- Mechanically compiled `candidate_replacement` pairs: {frozen["candidate_replacement_pairs"]}
- Purpose-required candidate/context cases: {frozen["candidate_case_count"]}
- Semantic obligations: {frozen["obligation_count"]}
- Fingerprint: `{frozen.get("fingerprint")}`

### Rule

{frozen["generation_rule"]}

### Obligations

{chr(10).join(obligation_lines) or "(none)"}

## Oracle residual (loaded only after freeze)

`F_oracle = C0 − C1`

{chr(10).join(residual_lines) or "(empty)"}

## Comparison

| metric | value |
| --- | --- |
| true positives | {comparison["true_positive_count"]} |
| false positives | {comparison["false_positive_count"]} |
| false negatives | {comparison["false_negative_count"]} |
| precision | {precision_display} ({precision}) |
| recall | {recall_display} ({recall}) |
| exact frontier match | {comparison["exact_frontier_match"]} |

True positives:

{_format_tuples(comparison["true_positives"])}

False positives:

{_format_tuples(comparison["false_positives"])}

False negatives:

{_format_tuples(comparison["false_negatives"])}

## Required interpretation

### 1. Can the semantic frontier be generated without C0?

Yes. The generator receives only a compiled C1 TaskView and the frozen purpose
contract. Candidate identities come from World IR joins. C0 is not an input.

### 2. What exactly created each obligation?

Each obligation is a demanded `acceptable_replacement(new, old, context)` for a
mechanically compiled `candidate_replacement` pair together with each
`deployment_environment` of a BOM item whose required `part_type` matches both
parts, when that exact tuple is not already established in SemanticWorld.

### 3. Is each obligation tied to a declared computation/purpose rather than generic missing world knowledge?

Yes. Obligations are not "all semantic facts missing from World IR". They are
viability judgments required by purpose `{frozen["purpose"]["id"]}` for concrete
mechanically generated replacement cases. Unrelated missing facts do not appear.

### 4. Does resolving an obligation remove it mechanically?

Yes. Inserting the demanded tuple into a temporary copy of C1 removes that
obligation on regeneration. Remaining unresolved demand is unchanged.

### 5. Do new relevant candidates create new obligations?

Yes. Adding one extra `candidate_replacement` that falls under the purpose and
lacks an `acceptable_replacement` judgment adds exactly one obligation.

### 6. Does irrelevant world growth leave it unchanged?

Yes. Additional part, listing, and BOM records that do not create a new
purpose-required candidate/context case leave the operational frontier unchanged.

### 7. Does the operational frontier exactly match the historical oracle residual for frozen S1?

{"Yes." if comparison["exact_frontier_match"] else "No."} Precision is {comparison["true_positive_count"]}/{frozen["obligation_count"] or 0}; recall is {comparison["recall"]}. The operational rule uses every mechanically represented BOM context of the matching part type. The hidden C0 residual encodes a narrower engineering-note restriction that is not present as compiled World IR. The extra operational demand is a false positive relative to C0, not a generator read of C0.

### 8. What remaining role did C0 play?

Evaluation oracle only. It was loaded after `operational_frontier.json` was
serialized, to compute `F_oracle = C0 − C1` and score the frozen obligations.
C0 was not a constructor input.

## Counterfactual checks

Recorded by `tests/semantic_integration/test_operational_frontier.py`:

1. Already-resolved: inserting one required `acceptable_replacement` into a C1 copy removes that obligation.
2. Additional candidate: one extra purpose-covered `candidate_replacement` adds one obligation. It is not added to C0 and is not scored against the frozen oracle.
3. Irrelevant growth: unrelated BOM/part/listing records leave the frontier unchanged.

## LLM semantic authoring (not implemented in this run)

These surfaces are identified only. This experiment did not invoke a model.

### ASSERTION AUTHORING

Grounded tuples from bounded evidence.

Already empirically exercised: the authorized BOM C2 campaign inserted two
packet-grounded `acceptable_replacement` ACCEPT judgments. This run does not
repeat that.

### VOCABULARY AUTHORING

Candidate relation names, roles, and meanings demanded by unresolved distinctions.

Hypothesis only. Not implemented or tested here.

### DERIVATION AUTHORING

Candidate deterministic rules over existing relations.

Hypothesis only. C1's SQL derivations were human-authored earlier; this run
does not ask a model to propose rules.

### ABSTRACTION AUTHORING

Candidate reusable semantic concepts over lower-level evidence.

Hypothesis only. Not implemented or tested here.

Currently only bounded assertion authoring has been exercised directly.
"""


def _format_tuples(rows: list[list[Any]]) -> str:
    if not rows:
        return "(none)"
    return "\n".join(
        "- `" + ", ".join(str(item) for item in row) + "`" for row in rows
    )


def write_report(
    frozen_path: Path = FROZEN_PATH,
    report_path: Path | None = None,
) -> Path:
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    evaluation = evaluate(frozen_path)
    destination = report_path or frozen_path.with_name("report.md")
    destination.write_text(render_report(frozen, evaluation), encoding="utf-8")
    return destination


if __name__ == "__main__":
    frozen = json.loads(FROZEN_PATH.read_text(encoding="utf-8"))
    evaluation = evaluate()
    report_path = FROZEN_PATH.with_name("report.md")
    report_path.write_text(render_report(frozen, evaluation), encoding="utf-8")
    print(json.dumps({**evaluation, "report": str(report_path)}, indent=2, sort_keys=True))
