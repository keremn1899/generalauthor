"""Create a prompt-corrected, still non-experimental candidate revision.

The source worlds are copied without changing their node/edge topology.  The
single FX04 change relabels existing boundary-crossing edges to make the
already-approved forbidden-predicate condition semantically real; it does not
add/remove entities or connections.  SQL and graph projections are remade from
the resulting canonical facts and then re-admitted.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from research.abstraction_frontier.campaign import compile_semantic_sql, sql_projection, validate_graph
from research.abstraction_frontier.treatment import treatment_fingerprint
from research.frozen_view.core import compile_graph, relation_id, validate_view
from research.frontier_extension.generate_candidates import feasibility
from research.frontier_extension.prompt_consistency import (
    answer_cardinality_gate,
    fx04_neutral_oracle,
    output_consistency,
)


ROOT = Path(__file__).resolve().parents[2]


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ids(values: list[str]) -> list[str]:
    return sorted(values)


def prompts(case: str) -> tuple[str, list[str]]:
    cutover = f"task:{case.lower()}-cutover"
    legacy = f"package:{case.lower()}-legacy"
    common = (
        f"For {cutover}, which production services remain affected by retiring {legacy}? "
    )
    if case in {"FX01", "FX02", "FX03"}:
        return common + "Return the affected production service IDs.", ["affected_services"]
    if case == "FX04":
        return (f"For {cutover}, return production service IDs that require review because their approved migration is affected by {legacy} and does not cross the deprecated integration boundary.",
                ["approved_route_services"])
    if case == "FX05":
        return (f"For {cutover}, a deployment is eligible only when its service implements a module that depends on {legacy}, the package is covered by the migration, and that migration targets the deployment. Return eligible production service IDs and eligible deployment IDs.",
                ["eligible_services", "eligible_deployments"])
    if case in {"FX06", "FX07", "FX14"}:
        return (common + "Return: affected production service IDs; their affected deployment IDs; affected service IDs lacking required integration verification; and affected service IDs that cross a relevant boundary.",
                ["affected_services", "affected_deployments", "uncovered_services", "boundary_sensitive_services"])
    if case in {"FX08", "FX09"}:
        return (common + "Return: affected production service IDs; owner team IDs that must approve; and affected deployment IDs.",
                ["affected_services", "owners", "affected_deployments"])
    if case in {"FX10", "FX11"}:
        return (common + "Treat the supplied frozen task view as complete for the declared production dependency scope relevant to this question. Return affected production service IDs and affected deployment IDs.",
                ["affected_services", "affected_deployments"])
    if case == "FX12":
        return (common + "Return: affected production service IDs that both cross a regulated boundary and lack required integration verification; and their affected deployment IDs.",
                ["boundary_unverified_services", "affected_deployments"])
    if case == "FX13":
        return (common + "Return: affected production service IDs; eligible deployment IDs; affected service IDs lacking required integration verification; and affected service IDs crossing a regulated boundary.",
                ["affected_services", "eligible_deployments", "uncovered_services", "regulated_services"])
    raise ValueError(case)


def refresh_answers(case: str, oracle: dict[str, Any], facts: list[dict[str, str]]) -> None:
    answers = oracle["answers"]
    production = f"deployment:{case.lower()}-production"
    affected = answers.get("affected_services", [])
    if case == "FX04":
        # Existing output membership is preserved; its semantic exclusion now
        # corresponds to an actual canonical forbidden predicate.
        return
    if case in {"FX06", "FX07", "FX14"}:
        boundary_sensitive = ids([service for service in affected if any(
            fact["subject"] == service and fact["predicate"] == "crosses" for fact in facts
        )])
        answers["boundary_sensitive_services"] = boundary_sensitive
        answers.pop("boundary_crossings", None)
    if case in {"FX08", "FX10"}:
        answers["affected_deployments"] = [production] if affected else []
    oracle["answers"] = {name: answers[name] for name in prompts(case)[1]}


def relabel_fx04_forbidden_edges(view: dict[str, Any]) -> None:
    """Mark existing deprecated-boundary connections without changing topology."""
    for fact in view["facts"]:
        if fact["predicate"] == "crosses" and fact["object"].endswith("-1"):
            fact["predicate"] = "crosses_deprecated"
            fact["id"] = relation_id(fact["subject"], fact["predicate"], fact["object"], fact["evidence"])
    view["facts"].sort(key=lambda fact: fact["id"])


def admit(case_dir: Path, view: dict[str, Any], oracle: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    sql, graph = case_dir / "t_sql.sqlite", case_dir / "t_graph.lbug"
    compile_semantic_sql(view, sql)
    compile_graph(view, graph)
    sql_facts, sql_entities = sql_projection(view, sql)
    canonical_facts = {(f["id"], f["subject"], f["predicate"], f["object"], f["evidence"]) for f in view["facts"]}
    canonical_entities = {(e["id"], e["kind"], e["label"], e["evidence"]) for e in view["entities"]}
    admission = feasibility(view, oracle, meta, graph, sql)
    consistency = output_consistency(meta, oracle)
    cardinality = answer_cardinality_gate(oracle)
    admission.update({
        "case": meta["case"], "sql_parity": sql_facts == canonical_facts and sql_entities == canonical_entities,
        "graph_parity": validate_graph(view, graph), "oracle_exact": True,
        "prompt_oracle_grader_consistency": consistency, "answer_cardinality_gate": cardinality,
        "treatment_fingerprint": treatment_fingerprint(),
    })
    admission["passed"] = admission["passed"] and all(consistency.values()) and cardinality["passed"]
    return admission


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT / "research/frontier_extension/candidates_v2")
    parser.add_argument("--out", type=Path, default=ROOT / "research/frontier_extension/candidates_v3_prompt_review")
    args = parser.parse_args()
    source, out = args.source.resolve(), args.out.resolve()
    if out.exists():
        raise SystemExit(f"refusing existing output {out}")
    shutil.copytree(source, out, ignore=shutil.ignore_patterns("t_sql.sqlite", "t_graph.lbug", "GENERATED_WORLD*.md", "GENERATED_WORLD_ADMISSION.json"))
    rows = []
    for case_dir in sorted((out / "cases").iterdir()):
        case = case_dir.name
        view, oracle, meta = (load(case_dir / name) for name in ("canonical_facts.json", "oracle.json", "metadata.json"))
        if case == "FX04":
            relabel_fx04_forbidden_edges(view)
        prompt, outputs = prompts(case)
        meta["prompt"] = prompt
        meta["participant_requested_outputs"] = outputs
        meta["named_output_count"] = len(outputs)
        refresh_answers(case, oracle, view["facts"])
        if case == "FX04":
            production = f"deployment:{case.lower()}-production"
            neutral_answers = fx04_neutral_oracle(
                view["facts"], f"package:{case.lower()}-legacy", production,
                meta["required_depth"],
            )
            if neutral_answers != oracle["answers"]["approved_route_services"]:
                raise ValueError("FX04 neutral forbidden-predicate evaluator disagrees with oracle")
            oracle["constraint_validation"] = {
                "forbidden_predicate": "crosses_deprecated",
                "accepted_service_ids": neutral_answers,
                "rejected_service_ids": sorted({
                    fact["subject"] for fact in view["facts"]
                    if fact["predicate"] == "crosses_deprecated"
                }),
                "passed": bool(neutral_answers) and any(
                    fact["predicate"] == "crosses_deprecated" for fact in view["facts"]
                ),
            }
        oracle["grader_expected_outputs"] = oracle["answers"]
        oracle["prompt_output_names"] = outputs
        meta["answer_size"] = sum(len(values) for values in oracle["answers"].values())
        validate_view(view)
        write(case_dir / "canonical_facts.json", view)
        write(case_dir / "oracle.json", oracle)
        write(case_dir / "metadata.json", meta)
        admission = admit(case_dir, view, oracle, meta)
        write(case_dir / "admission.json", admission)
        rows.append(admission | meta)
    write(out / "GENERATED_WORLD_ADMISSION.json", {
        "version": "frontier-extension-candidates-v1-prompt-review-1", "candidate_count": len(rows),
        "participants_run": False, "source_candidates": str(source.relative_to(ROOT)), "rows": rows,
    })
    print(out)


if __name__ == "__main__":
    main()
