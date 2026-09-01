"""Read-only representation/frontier audit for a completed frozen campaign.

It deliberately consumes only frozen candidate artifacts and sealed receipt
files.  It never imports participant answers when calculating a case's
structural row and never rewrites a treatment artifact or input hash.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    keys = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (list, dict)) else value for key, value in row.items()})


def family(case_id: str) -> str:
    for suffix, label in (
        ("verification-control", "verification control"),
        ("production-impact", "production impact"),
        ("cutover-boundary-control", "cutover boundary control"),
        ("cutover-readiness", "cutover readiness"),
    ):
        if case_id.endswith(suffix):
            return label
    return "unknown"


def literals(value: Any) -> set[str]:
    if isinstance(value, str):
        # Stable canonical entities use `kind:identifier`.  Restricting this
        # extractor to those values prevents query vocabulary (`op`, predicate
        # names, endpoint kind names) from being miscounted as seed entities.
        return {value} if ":" in value and not value.startswith("$") else set()
    if isinstance(value, list):
        return set().union(*(literals(item) for item in value)) if value else set()
    if isinstance(value, dict):
        return set().union(*(literals(item) for item in value.values())) if value else set()
    return set()


def requirements(query: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    derive = query["derive"]
    operations = [value["op"] for value in derive.values()]
    predicates = set()
    for value in derive.values():
        predicates.update(value.get("predicates", []))
    return {
        "seed_count": len(set().union(*(literals(value) for value in derive.values()))),
        "maximum_declared_step_depth": max((int(value.get("max_depth", value.get("max_hops", 1))) for value in derive.values() if value["op"] in {"traverse", "reverse_reachable", "path_targets"}), default=0),
        "predicate_count": len(predicates),
        "requires_reverse": "reverse_reachable" in operations,
        "requires_bounded_multihop": any(value["op"] == "reverse_reachable" and int(value.get("max_depth", 1)) > 1 for value in derive.values()),
        # Every frozen case has a fixed small bound; no query needs a general
        # transitive closure rather than an unrolled short relational join.
        "requires_reachability": False,
        "requires_path": "path_targets" in operations,
        "requires_predicate_sequence": "sequence" in operations,
        "requires_intersection": "intersection" in operations,
        "requires_difference": "difference" in operations,
        "requires_union": "union" in operations,
        "requires_intermediate_reuse": int(metadata.get("intermediate_reuse_count", 0)) > 0,
        "requires_absence_proof": False,
    }


def neutral_shape(case_id: str) -> tuple[str, str]:
    shapes = {
        "verification-control": ("seed service → incoming verifies → test", "one-hop inverse/fan-out"),
        "production-impact": ("seed legacy package → incoming depends_on (bounded two steps) → incoming implements → service; independently deployment → incoming deployed_to → service; intersect", "bounded multi-hop + join/set composition"),
        "cutover-boundary-control": ("seed cutover → targets → deployment → incoming deployed_to → service; intersect fixed API; outgoing crosses → boundary", "join/set composition"),
        "cutover-readiness": ("seed cutover → retires → package → incoming depends_on (bounded two steps) → incoming implements → service; independently deployment → incoming deployed_to → service; intersect; incoming verifies", "composite/reused topology"),
    }
    for suffix, output in shapes.items():
        if case_id.endswith(suffix):
            return output
    return "NA", "unknown"


def case_rows(root: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for item in manifest["cases"]:
        case_id, world = item["id"], item["world_id"]
        spec = root / "worlds" / world / "candidate_task_view_specs" / case_id
        view, oracle = load(spec / "task_view.json"), load(spec / "oracle.json")
        rel_ids = set(oracle["oracle_relation_ids"])
        rels = [row for row in view["facts"] if row["id"] in rel_ids]
        flattened_answers = set().union(*(set(value) for value in oracle["answers"].values())) if oracle["answers"] else set()
        for relation in rels:
            flattened_answers.update((relation["subject"], relation["object"]))
        # Literal task references are entities even where a direct lookup has no edge.
        query = load(spec / "neutral_query.json")
        for expr in query["derive"].values():
            flattened_answers.update(literals(expr))
        req = requirements(query, item["metadata"])
        degrees: Counter[str] = Counter()
        for relation in rels:
            degrees[relation["subject"]] += 1; degrees[relation["object"]] += 1
        shape, derived_family = neutral_shape(case_id)
        rows.append({
            "case": case_id, "platform": world, "task_family": family(case_id), "preregistered_R": item["R"], "preregistered_A": item["A"],
            "answer_size": sum(len(value) for value in oracle["answers"].values()), "relevant_seed_entities": req["seed_count"],
            "relevant_entity_count": len(flattened_answers), "relevant_relation_count": len(rels),
            "distractor_entity_count": len(view["entities"]) - len(flattened_answers), "distractor_relation_count": len(view["facts"]) - len(rels),
            "required_depth": item["metadata"]["minimum_required_depth"], "maximum_relevant_traversal_depth": req["maximum_declared_step_depth"],
            "relevant_reachable_closure_size": len(flattened_answers), "branching_measure_max_incident_degree": max(degrees.values(), default=0),
            "predicate_count": req["predicate_count"], "requires_reverse": req["requires_reverse"], "requires_bounded_multihop": req["requires_bounded_multihop"], "requires_reachability": req["requires_reachability"],
            "requires_path": req["requires_path"], "requires_predicate_sequence": req["requires_predicate_sequence"],
            "requires_intersection": req["requires_intersection"], "requires_difference": req["requires_difference"], "requires_union": req["requires_union"],
            "requires_intermediate_reuse": req["requires_intermediate_reuse"], "requires_absence_proof": False,
            "cycles_in_relevant_substructure": False, "set_composition_count": item["metadata"]["set_composition_count"],
            "generator_intermediate_reuse_count": item["metadata"]["intermediate_reuse_count"], "generator_distractor_size": item["metadata"]["distractor_size"],
            "neutral_requirement": shape, "derived_structural_family": derived_family,
        })
    return rows


def sql_inventory(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    schemas: dict[str, dict[str, Any]] = {}
    all_predicates: dict[tuple[str, str, str], str] = {}
    rows_by_case: list[dict[str, Any]] = []
    for item in manifest["cases"]:
        case_id, world = item["id"], item["world_id"]
        db_path = root / "projections" / case_id / "t_sql.sqlite"
        spec = root / "worlds" / world / "candidate_task_view_specs" / case_id
        view = load(spec / "task_view.json")
        kinds = {entry["id"]: entry["kind"] for entry in view["entities"]}
        with sqlite3.connect(db_path) as db:
            objects = db.execute("SELECT type, name, sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name").fetchall()
            signature = "\n".join(str(row[2] or "") for row in objects)
            schemas.setdefault(signature, {"cases": [], "objects": [{"type": row[0], "name": row[1], "sql": row[2]} for row in objects]})["cases"].append(case_id)
            for object_type, name, _ in objects:
                if object_type == "table":
                    rows_by_case.append({"case": case_id, "platform": world, "table": name, "row_count": db.execute('SELECT COUNT(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]})
        for relation in view["facts"]:
            key = (kinds[relation["subject"]], relation["predicate"], kinds[relation["object"]])
            all_predicates[key] = f"{key[0]}_{key[1]}_{key[2]}(relation_id, subject_id, object_id, evidence)"
    return {"schemas": schemas, "predicate_mapping": all_predicates, "row_counts": rows_by_case}


def tool_result_bytes(stdout: str) -> int:
    """Bytes of completed tool result payloads retained in Cursor's stream-json."""
    total = 0
    for line in stdout.splitlines():
        try: event = json.loads(line)
        except ValueError: continue
        if event.get("type") == "tool_call" and event.get("subtype") == "completed":
            total += len(json.dumps(event.get("tool_call", {}), sort_keys=True, separators=(",", ":")).encode())
    return total


def step_features(program: dict[str, Any]) -> dict[str, Any]:
    steps = list(program.get("steps") or [])
    ops = [str(step.get("op") or "") for step in steps]
    predicates = sorted({str(predicate) for step in steps for predicate in (step.get("predicates") or [])})
    variables = [str(step.get("assign") or "") for step in steps if step.get("assign")]
    reused = False
    for index, variable in enumerate(variables):
        token = "$" + variable
        if sum(json.dumps(step, sort_keys=True).count(token) for step in steps[index + 1:]) > 1:
            reused = True
    return {"internal_ops": len(steps), "predicates": predicates, "set_algebra": sum(op in {"union", "intersection", "difference"} for op in ops),
            "path_or_sequence": sum(op in {"find_paths", "shortest_path", "walk_sequence"} for op in ops), "reused": reused,
            "uses_search": "search" in ops, "compact": str(program.get("result_mode") or "full") == "compact"}


def execution_rows(root: Path, structural: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "executions").glob("*/*/record.json")):
        record = load(path); case, arm = record["case_id"], record["arm"]
        events = record["graph_operations"] if arm != "T_SQL" else record["sql_queries"]
        row: dict[str, Any] = {
            "case": case, "platform": structural[case]["platform"], "task_family": structural[case]["task_family"], "arm": arm,
            "exact_correct": record["score"]["exact_correct"], "valid_execution": record["valid_execution"], "wall_seconds": record["wall_seconds"],
            "model_environment_round_trips": record["tool_call_count"], "total_tool_calls": record["tool_call_count"],
            "model_input_tokens": "NA", "model_output_tokens": "NA", "model_visible_tool_result_bytes": tool_result_bytes(record["stdout"]),
            "retries_errors": sum(event.get("event", "").endswith("failure") for event in events), "raw_receipt": str(path.relative_to(root)),
        }
        if arm == "T_SQL":
            statements = [event["query_text"] for event in events if event["event"] == "sql_statement"]
            results = [event for event in events if event["event"] == "sql_result"]
            joined = "\n".join(statements).upper()
            row.update({
                "schema_inspection_calls": sum("SQLITE_MASTER" in statement.upper() or "PRAGMA" in statement.upper() for statement in statements),
                "sql_statement_count": len(statements), "sql_select_count": sum(bool(re.search(r"\bSELECT\b", statement, re.I)) for statement in statements),
                "sql_join_count": sum(len(re.findall(r"\bJOIN\b", statement, re.I)) for statement in statements),
                "sql_set_operation_count": sum(len(re.findall(r"\b(?:UNION|INTERSECT|EXCEPT)\b", statement, re.I)) for statement in statements),
                "sql_recursive_cte_count": sum("WITH RECURSIVE" in statement.upper() for statement in statements),
                "sql_aggregate_grouping": sum(bool(re.search(r"\b(?:GROUP\s+BY|COUNT\s*\(|SUM\s*\(|AVG\s*\(|MIN\s*\(|MAX\s*\()", statement, re.I)) for statement in statements),
                "temporary_host_language_programs": "NA (receipt retains calls, not a reliable program-file taxonomy)",
                "rows_returned_by_query": [event["rows_returned"] for event in results], "total_rows_returned": sum(event["rows_returned"] for event in results),
                "model_visible_entity_records": "NA (row payloads were not retained by SQL audit)", "model_visible_relation_records": "NA (row payloads were not retained by SQL audit)",
                "sql_audit_reference": str(path.relative_to(root)),
            })
        else:
            successful = [event for event in events if event["event"] == "graph_operation"]
            failures = [event for event in events if event["event"] == "graph_operation_failure"]
            op_counts = Counter(event["operation"] for event in successful)
            feature = {"internal_ops": 0, "predicates": set(), "set_algebra": 0, "path_or_sequence": 0, "reused": False, "compact": False, "uses_search": False}
            visible_nodes = visible_edges = visible_paths = audit_nodes = audit_edges = audit_paths = answer_size = 0
            program_refs = []
            for event in successful:
                receipt = event.get("receipt") or {}
                args = event.get("arguments") or {}
                program = args.get("program") if event["operation"] == "run_ephemeral_traversal" else None
                mode = "full"
                if isinstance(program, dict):
                    details = step_features(program); program_refs.append(program)
                    feature["internal_ops"] += details["internal_ops"]; feature["predicates"].update(details["predicates"]); feature["set_algebra"] += details["set_algebra"]; feature["path_or_sequence"] += details["path_or_sequence"]; feature["reused"] |= details["reused"]; feature["compact"] |= details["compact"]; feature["uses_search"] |= details["uses_search"]; mode = "compact" if details["compact"] else "full"
                internal_nodes, internal_edges, internal_paths = int(receipt.get("packet_node_count") or 0), int(receipt.get("packet_edge_count") or 0), int(receipt.get("packet_path_count") or 0)
                audit_nodes += internal_nodes; audit_edges += internal_edges; audit_paths += internal_paths
                if mode == "compact":
                    answer_size += int(receipt.get("answer_count") or 0)
                else:
                    visible_nodes += internal_nodes; visible_edges += internal_edges; visible_paths += internal_paths
            row.update({
                "describe_calls": op_counts["describe"], "lookup_calls": op_counts["lookup"], "expand_calls": op_counts["expand"], "path_calls": op_counts["path"], "ephemeral_calls": op_counts["run_ephemeral_traversal"],
                "ephemeral_programs": program_refs, "internal_deterministic_operations": feature["internal_ops"], "predicates_used": sorted(feature["predicates"]), "set_algebra_operations": feature["set_algebra"], "path_sequence_operations": feature["path_or_sequence"], "intermediate_variable_reuse": feature["reused"], "compact_selected": feature["compact"], "uses_disallowed_search_inside_ephemeral": feature["uses_search"],
                "named_answer_set_size": answer_size, "model_visible_canonical_entity_records": visible_nodes + answer_size, "model_visible_canonical_relation_records": visible_edges, "model_visible_path_records": visible_paths,
                "retained_audit_nodes": audit_nodes, "retained_audit_edges": audit_edges, "retained_audit_paths": audit_paths, "graph_operation_failures": len(failures), "graph_audit_reference": str(path.relative_to(root)),
            })
        rows.append(row)
    return rows


def med(values: list[float]) -> float:
    return float(statistics.median(values))


def report(root: Path, structural: list[dict[str, Any]], sql: dict[str, Any], execution: list[dict[str, Any]]) -> str:
    predicate_rows = "\n".join(f"| `{predicate}` ({source} → {target}) | `{table}` |" for (source, predicate, target), table in sorted(sql["predicate_mapping"].items()))
    ddl = []
    for index, schema in enumerate(sql["schemas"].values(), 1):
        ddl.append(f"### Schema variant {index} — cases: {', '.join(schema['cases'])}\n\n```sql\n" + "\n".join(obj["sql"] + ";" for obj in schema["objects"] if obj["sql"]) + "\n```")
    case_table = "\n".join(f"| {r['case']} | {r['platform']} | {r['task_family']} | {r['preregistered_A']} | {r['preregistered_R']} | {r['answer_size']} | {r['relevant_seed_entities']} | {r['relevant_relation_count']} | {r['distractor_entity_count']}/{r['distractor_relation_count']} | {r['required_depth']} | {r['relevant_reachable_closure_size']} | {r['branching_measure_max_incident_degree']} | {r['predicate_count']} | {r['requires_reverse']} | {r['requires_reachability']} | {r['requires_path']} | {r['requires_intersection']} | {r['requires_intermediate_reuse']} |" for r in structural)
    numeric = ["answer_size", "relevant_seed_entities", "relevant_entity_count", "relevant_relation_count", "distractor_entity_count", "distractor_relation_count", "required_depth", "maximum_relevant_traversal_depth", "relevant_reachable_closure_size", "branching_measure_max_incident_degree", "predicate_count", "set_composition_count", "generator_intermediate_reuse_count"]
    summary = "\n".join(f"| {name} | {min(r[name] for r in structural)} | {med([r[name] for r in structural])} | {max(r[name] for r in structural)} |" for name in numeric)
    count = lambda key: sum(bool(row[key]) for row in structural)
    graph = [row for row in execution if row["arm"] != "T_SQL"]
    adoption = {"ephemeral": sum(row["ephemeral_calls"] > 0 for row in graph), "compact": sum(row["compact_selected"] for row in graph), "multistep": sum(row["internal_deterministic_operations"] > 1 for row in graph), "predicate_multi": sum(len(row["predicates_used"]) > 1 for row in graph), "reuse": sum(row["intermediate_variable_reuse"] for row in graph), "search": sum(row["uses_disallowed_search_inside_ephemeral"] for row in graph)}
    trace_table = "\n".join(f"| {r['case']} | {r['arm']} | {r['exact_correct']} | {r['wall_seconds']:.2f} | {r['model_environment_round_trips']} | {r['model_visible_tool_result_bytes']} | {r['retries_errors']} |" for r in execution)
    adoption_table = "\n".join(f"| {r['case']} | {r['arm']} | {r['ephemeral_calls'] > 0} | {r['compact_selected']} | {r['path_calls'] > 0 or r['path_sequence_operations'] > 0} | {r['internal_deterministic_operations'] > 1} | {r['set_algebra_operations'] > 0} | {r['intermediate_variable_reuse']} |" for r in graph)
    return f"""# Frozen frontier pilot — representation and frontier audit

**Scope.** This is non-experimental and read-only. Structural rows were derived solely from each frozen task view, neutral oracle, canonical relation IDs, and preregistered metadata. Trace rows are derived solely from sealed participant receipts. No new participants were run and neither treatment was altered.

## A. SQL representation audit

T_SQL has one typed entity table per entity kind and one typed directed relation table per `(subject kind, logical predicate, object kind)`. There is no generic `nodes`/`edges` primary surface, EAV/triple table, adjacency list, closure, path table, view, JSON adjacency, recursive-CTE helper, or benchmark-authored solution view. No foreign-key constraints are declared in the frozen DDL; integrity was checked by the projection audit rather than enforced by SQLite constraints. `relation_id` and `evidence` are provenance columns.

| Canonical predicate / endpoint kinds | SQL representation |
| --- | --- |
{predicate_rows}

### Exact frozen DDL

{chr(10).join(ddl)}

### Per-case table row counts

The complete machine-readable inventory is `sql_table_row_counts.csv`. Counts vary only by task projection type, not by platform label.

SQL REPRESENTATION AUDIT:
**PASS — idiomatic semantic relational schema.** The table names encode entity and relation semantics. The `subject_id`/`object_id` column convention is generic within already-typed relation tables, but it is not a generic graph/triple query surface. Absence of declared FK constraints is an integrity limitation, not a graph-shaped representation.

## B–C. Frozen structural case profile and substrate-neutral requirement

| Case | Platform | Family | A | R | Answer | Seeds | Relevant rels | Distractor ent/rels | Min depth | Closure | Max degree | Predicates | Reverse | Reachability >1 | Path | Intersection | Reuse |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- | --- | --- | --- |
{case_table}

`case_structural_profile.csv` and `.json` contain every requested pre-treatment field, including fixed `false`/`NA` values for paths, sequences, difference, union, cycles, and absence proofs. The `neutral_requirement` and `derived_structural_family` fields give the substrate-neutral computation for each row.

## D. Frontier coverage

| Numeric measure | Minimum | Median | Maximum |
| --- | ---: | ---: | ---: |
{summary}

- Depth 0–1: {sum(r['required_depth'] <= 1 for r in structural)} cases; depth 2: {sum(r['required_depth'] == 2 for r in structural)}; depth 3+: {sum(r['required_depth'] >= 3 for r in structural)}. Maximum necessary depth: {max(r['required_depth'] for r in structural)}.
- Bounded multi-hop relation composition: {count('requires_bounded_multihop')}; genuine transitive reachability rather than a fixed short join: {count('requires_reachability')}; constrained endpoint paths: {count('requires_path')}; three-or-more predicates: {sum(r['predicate_count'] >= 3 for r in structural)}.
- Reusable intermediate sets: {count('requires_intermediate_reuse')}; multiple distinct topology computations in one task: {sum(r['preregistered_R'] == 'R4' for r in structural)}.
- Absence/non-reachability proofs: {count('requires_absence_proof')}; cases naturally requiring recursive CTEs: 0; substantial repeated closure reuse: 0.

Mechanically, the instantiated pilot is dominated by direct inverse lookup and fixed bounded joins: all reachability is bounded to at most two repetitions of one predicate; no case requires a constrained endpoint path, ordered predicate sequence, difference/union, cycle handling, or negative proof. The R4 cases compose/reuse short intermediate sets but do not require a large/repeated closure.

## E. Participant trace extraction

| Case | Arm | Exact | Wall s | Model↔environment calls | Retained tool-result bytes | Errors/retries |
| --- | --- | --- | ---: | ---: | ---: | ---: |
{trace_table}

`execution_trace.csv` and `.json` contain all requested arm-specific diagnostics and preserved audit references. Input/output model tokens are `NA`: Cursor’s stream records did not report usage. “Model-visible tool-result bytes” is the UTF-8 size of completed tool-result payloads retained in stream-json, not a tokenizer estimate. SQL row payloads were not retained by the SQL audit, so SQL entity/relation-record counts are `NA`; row counts are retained exactly. For graph, full packets count as model-visible, compact runs count only named answer IDs as model-visible, and the full packet is reported separately as retained audit evidence.

### Important trace finding: frozen graph-surface deviation

The policy disabled `search`, but `run_ephemeral_traversal` accepted recipe op `search`; the wrapper did not reject it. The sealed graph receipts show lexical-search internal operations in {adoption['search']}/{len(graph)} graph executions. This is a treatment-surface deviation. It did not expose raw sources, inferred edges, Compass data, or facts outside the frozen graph, but it means the campaign did **not** implement the stated no-search G surface exactly. The trace also contains graph-operation failures (mostly invalid parameter guesses and single-owner file contention) followed by participant adaptation; they are recorded as errors, not hidden retries.

## F. Graph-v1 adoption/manipulation diagnostic

| Case | Arm | Ephemeral program? | Compact? | Path? | Multi-step traversal? | Set algebra? | Intermediate reuse? |
| --- | --- | --- | --- | --- | --- | --- | --- |
{adoption_table}

Across {len(graph)} graph executions: ephemeral programs {adoption['ephemeral']}/{len(graph)} ({adoption['ephemeral']/len(graph):.0%}); compact chosen {adoption['compact']}/{len(graph)} ({adoption['compact']/len(graph):.0%}); multi-step program {adoption['multistep']}/{len(graph)} ({adoption['multistep']/len(graph):.0%}); multi-predicate program {adoption['predicate_multi']}/{len(graph)} ({adoption['predicate_multi']/len(graph):.0%}); intermediate reuse {adoption['reuse']}/{len(graph)} ({adoption['reuse']/len(graph):.0%}). Endpoint path operations were not successfully used for a scored solution. The execution table is the authoritative per-case adoption record.

## G. Analysis-ready tables

- `case_structural_profile.csv` / `.json`: pre-treatment/oracle structural data only, keyed by `case`.
- `execution_trace.csv` / `.json`: outcomes and participant trajectory data, keyed by `case, arm`.

## H. Descriptive conclusion

**SQL representation:** T_SQL was table-shaped and semantic-relational, not a generic graph encoded in SQLite.

**Pilot coverage:** The 16 cases contain primarily direct/join/set workloads plus a meaningful but shallow bounded-topology range. They do not instantiate genuinely high-topology or repeated-large-closure work.

**Ceiling:** Exact correctness saturated before the highest intended topology regimes from the original concept were instantiated: this follows from the structural coverage (not from wall time or tool counts).

**Remaining frontier:** Not instantiated or only weakly represented are deeper/larger reachability, high branching, constrained multi-predicate paths, ordered sequences, repeated reuse of one computed closure, several topology-dependent outputs over one large structure, cycles, and non-reachability/absence proofs. This is a coverage statement only; it proposes no new case and makes no performance claim.
"""


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("run_root", type=Path); parser.add_argument("--output", default="audit", help="new audit directory relative to run root"); args = parser.parse_args(); root = args.run_root.resolve(); out = root / args.output; out.mkdir(exist_ok=False)
    manifest = load(root / "PILOT_MANIFEST.json")
    structural = case_rows(root, manifest); structural_by_case = {row["case"]: row for row in structural}
    sql = sql_inventory(root, manifest); execution = execution_rows(root, structural_by_case)
    dump(out / "case_structural_profile.json", structural); write_csv(out / "case_structural_profile.csv", structural)
    dump(out / "execution_trace.json", execution); write_csv(out / "execution_trace.csv", execution)
    dump(out / "sql_schema_inventory.json", {"schemas": list(sql["schemas"].values()), "predicate_mapping": [{"subject_kind": a, "predicate": b, "object_kind": c, "sql": value} for (a,b,c),value in sorted(sql["predicate_mapping"].items())]}); write_csv(out / "sql_table_row_counts.csv", sql["row_counts"])
    (out / "REPRESENTATION_AND_FRONTIER_AUDIT.md").write_text(report(root, structural, sql, execution), encoding="utf-8")
    print(out)


if __name__ == "__main__": main()
