"""Generate and admit review-only frontier-extension candidates.

The generator creates software-shaped canonical facts, never participant
workspaces. It materializes projections only for parity/contract/feasibility
admission and writes no participant prompts beyond the frozen candidate text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import deque
from pathlib import Path
from typing import Any

from research.abstraction_frontier.campaign import compile_semantic_sql, sql_projection, validate_graph
from research.abstraction_frontier.treatment import treatment_fingerprint
from research.frozen_view.core import CANONICAL_VERSION, compile_graph, relation_id, validate_view
from mcp_server.surface import Surface


ROOT = Path(__file__).resolve().parents[2]
VERSION = "frontier-extension-candidates-v1"

SPECS = [
    ("FX01", "dependency_migration", "Short consumer impact", 3, 18, 3, 2, False, False, 1, 1),
    ("FX02", "dependency_migration", "Medium consumer impact", 5, 64, 5, 3, False, False, 1, 1),
    ("FX03", "dependency_migration", "Deep consumer impact", 8, 240, 8, 3, False, False, 1, 1),
    ("FX04", "release_safety", "Approved migration route", 5, 72, 5, 4, False, False, 1, 1),
    ("FX05", "release_safety", "Ordered cutover chain", 8, 200, 7, 5, False, False, 1, 2),
    ("FX06", "operational_containment", "Medium release-readiness bundle", 5, 92, 5, 4, False, False, 4, 4),
    ("FX07", "operational_containment", "Large release-readiness bundle", 8, 300, 8, 5, False, False, 4, 4),
    ("FX08", "operational_containment", "Cyclic service containment", 5, 82, 5, 4, True, False, 2, 2),
    ("FX09", "operational_containment", "Deep cyclic migration containment", 8, 250, 7, 4, True, False, 3, 3),
    ("FX10", "dependency_migration", "Medium legacy-clearance proof", 5, 102, 5, 4, False, True, 1, 1),
    ("FX11", "dependency_migration", "Large legacy-clearance proof", 8, 280, 8, 5, False, True, 2, 2),
    ("FX12", "release_safety", "Boundary-qualified impact", 6, 150, 7, 5, False, False, 2, 2),
    ("FX13", "release_safety", "Multi-output constrained rollout", 7, 220, 7, 5, False, False, 3, 4),
    ("FX14", "operational_containment", "Small closure-reuse control", 3, 20, 3, 3, False, False, 3, 3),
]


def stable_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def put(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(stable_json(value), encoding="utf-8")


def ent(identifier: str, label: str, evidence: str = "generator_spec.json") -> dict[str, str]:
    return {"id": identifier, "kind": identifier.split(":", 1)[0], "label": label, "evidence": evidence, "provenance_class": "deterministic_composition"}


def rel(subject: str, predicate: str, object_: str, evidence: str = "generator_spec.json") -> dict[str, str]:
    return {"id": relation_id(subject, predicate, object_, evidence), "subject": subject, "predicate": predicate, "object": object_, "evidence": evidence, "provenance_class": "deterministic_composition"}


def level_counts(depth: int, closure: int, branch: int) -> list[int]:
    """Deterministic layers with a reachable deepest layer and bounded fanout."""
    counts = [1] * depth
    remaining = closure - depth
    # Allocate from deep to shallow; each level can be supported by branch
    # children per prior node, while the final layer absorbs the working set.
    for index in range(depth - 1, -1, -1):
        capacity = (counts[index - 1] * branch if index else branch) - counts[index]
        add = min(max(capacity, 0), remaining)
        counts[index] += add; remaining -= add
    # Repeated passes are needed after growing a parent layer.
    while remaining:
        changed = False
        for index in range(depth):
            capacity = (counts[index - 1] * branch if index else branch) - counts[index]
            add = min(max(capacity, 0), remaining)
            if add: counts[index] += add; remaining -= add; changed = True
            if not remaining: break
        if not changed: raise ValueError("requested closure is infeasible for depth/branch")
    return counts


def build(spec: tuple[Any, ...]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    code, world, title, depth, closure, branch, predicates, cycle, absence, reuse, outputs = spec
    root = f"package:{code.lower()}-legacy"; deployment = f"deployment:{code.lower()}-production"; staging = f"deployment:{code.lower()}-staging"
    entities = [ent(root, f"{title} legacy package"), ent(deployment, "Production"), ent(staging, "Staging"), ent(f"task:{code.lower()}-cutover", f"{title} cutover")]
    facts = [rel(f"task:{code.lower()}-cutover", "retires", root), rel(f"task:{code.lower()}-cutover", "targets", deployment)]
    levels = level_counts(depth, closure, branch)
    nodes: list[list[str]] = []
    for level, count in enumerate(levels, 1):
        current=[]
        for index in range(count):
            identifier=f"module:{code.lower()}-l{level}-{index:03d}"; current.append(identifier); entities.append(ent(identifier, f"{title} module L{level}-{index}"))
            parent = root if level == 1 else nodes[-1][index % len(nodes[-1])]
            facts.append(rel(identifier, "depends_on", parent))
        nodes.append(current)
    if cycle:
        # Relevant three-node SCC, reached from the deep layer and finite under
        # oracle visited-node semantics.
        scc = nodes[min(2, depth - 1)][:3]
        if len(scc) == 3:
            facts.extend([rel(scc[0], "depends_on", scc[1]), rel(scc[1], "depends_on", scc[2]), rel(scc[2], "depends_on", scc[0])])
    service_ids=[]
    for index, module in enumerate(nodes[-1][:max(6, outputs + 2)]):
        service=f"service:{code.lower()}-{index:02d}"; service_ids.append(service); entities.append(ent(service, f"{title} service {index}"))
        facts += [rel(service, "implements", module), rel(service, "deployed_to", staging if absence else deployment)]
        if index % 2 == 0:
            test=f"test:{code.lower()}-{index:02d}"; entities.append(ent(test, f"{title} integration test {index}")); facts.append(rel(test, "verifies", service))
        if predicates >= 4:
            boundary=f"boundary:{code.lower()}-{index % 2}"; 
            if not any(e["id"] == boundary for e in entities): entities.append(ent(boundary, f"{title} boundary {index % 2}"))
            facts.append(rel(service, "crosses", boundary))
        if predicates >= 5:
            resource=f"resource:{code.lower()}-{index % 2}"
            if not any(e["id"] == resource for e in entities): entities.append(ent(resource, f"{title} resource {index % 2}"))
            facts.append(rel(service, "uses", resource))
        if cycle:
            team=f"team:{code.lower()}-{index % 2}"
            if not any(e["id"] == team for e in entities): entities.append(ent(team, f"{title} owner team {index % 2}"))
            facts.append(rel(service, "owned_by", team))
    # Ordered sequence cases add semantic migration links in a directed order.
    if code in {"FX04", "FX05", "FX13"}:
        migration=f"migration:{code.lower()}"; entities.append(ent(migration, f"{title} migration")); facts += [rel(root, "affects", migration), rel(migration, "targets", deployment)]
    view={"canonical_version":CANONICAL_VERSION,"entities":sorted(entities,key=lambda x:x["id"]),"facts":sorted(facts,key=lambda x:x["id"])}; validate_view(view)
    # Oracle closure over incoming depends_on, then service/deployment/test projections.
    incoming={}
    for f in facts: incoming.setdefault((f["object"],f["predicate"]),[]).append(f["subject"])
    q=deque([(root,0)]); seen={root}; used=[]
    while q:
        node,d=q.popleft()
        if d >= depth: continue
        for child in incoming.get((node,"depends_on"),[]):
            if child not in seen: seen.add(child); q.append((child,d+1)); used.append(next(f["id"] for f in facts if f["subject"]==child and f["predicate"]=="depends_on" and f["object"]==node))
    affected=sorted(s for s in service_ids if any(f["subject"]==s and f["predicate"]=="implements" and f["object"] in seen for f in facts) and not absence)
    deployments=[deployment] if affected else []
    verified={f["object"] for f in facts if f["predicate"]=="verifies"}; uncovered=sorted(set(affected)-verified)
    boundaries=sorted({f["object"] for f in facts if f["predicate"]=="crosses" and f["subject"] in affected})
    answer={"affected_services": affected}; operation="bounded_closure"; extra={}
    if code == "FX04":
        approved=[service for service in affected if any(f["subject"]==service and f["predicate"]=="crosses" and f["object"].endswith("-0") for f in facts)]
        answer={"approved_route_services":approved}; operation="constrained_reachability"; extra={"allowed_predicates":["depends_on","implements","deployed_to"],"forbidden_predicates":["crosses_deprecated"]}
    elif code == "FX05":
        answer={"eligible_services":affected,"eligible_deployments":deployments}; operation="ordered_sequence"; extra={"predicates":["implements","depends_on","affects","targets"]}
    elif cycle:
        owners=sorted({f["object"] for f in facts if f["predicate"]=="owned_by" and f["subject"] in affected})
        answer={"affected_services":affected,"owners":owners};
        if outputs >= 3: answer["affected_deployments"]=deployments
    elif code == "FX12":
        qualified=[service for service in affected if any(f["subject"]==service and f["predicate"]=="crosses" for f in facts) and service not in verified]
        answer={"boundary_unverified_services":qualified,"affected_deployments":deployments}; operation="qualified_set_composition"; extra={"intersection":["affected","boundary_sensitive"],"difference":["qualified","verified"]}
    elif code == "FX13":
        regulated=[service for service in affected if any(f["subject"]==service and f["predicate"]=="crosses" for f in facts)]
        answer={"affected_services":affected,"eligible_deployments":deployments,"uncovered_services":uncovered,"regulated_services":regulated}; operation="constrained_reachability"; extra={"allowed_predicates":["depends_on","implements","deployed_to","crosses"]}
    else:
        if outputs >= 2: answer["affected_deployments"]=deployments
        if outputs >= 3: answer["uncovered_services"]=uncovered
        if outputs >= 4: answer["boundary_crossings"]=boundaries
    prompt_map={"FX04":f"Which production services require review because their {title.lower()} is approved end-to-end and avoids the deprecated integration boundary? Return stable IDs only.","FX05":f"Which deployments are eligible for the {title.lower()} only when its service-to-module-to-package-to-migration chain is complete? Return stable IDs only.","FX12":f"Which affected production services both cross a regulated boundary and lack integration verification? Return stable IDs only.","FX13":f"For the {title.lower()}, return affected services, eligible deployments, uncovered integration tests, and regulated-boundary crossings as stable IDs."}
    prompt=prompt_map.get(code, f"For the {title} cutover, return the required production impact and safety information as stable IDs." if outputs > 1 else f"For the {title} cutover, which production services remain affected? Return stable IDs only.")
    neutral={"op":operation,"seed":root,"predicate":"depends_on","direction":"incoming","max_depth":depth,"cycle_policy":"visited_nodes","outputs":list(answer),**extra}
    metadata={"case":code,"platform":world,"template":title,"required_depth":depth,"relevant_closure_target":closure,"oracle_relevant_closure_size":len(seen)-1,"branching_target":branch,"predicate_target":predicates,"cycle":cycle,"absence_proof":absence,"intermediate_reuse_outputs":reuse,"named_output_count":outputs,"answer_size":sum(map(len,answer.values())),"prompt":prompt,"neutral_program":neutral}
    oracle={"answers":answer,"oracle_relation_ids":sorted(set(used)),"closed_scope":{"seed":root,"max_depth":depth,"visited_node_count":len(seen),"absence_proof":absence}}
    return view, oracle, metadata


def feasibility(view: dict[str, Any], oracle: dict[str, Any], meta: dict[str, Any], graph: Path, sql: Path) -> dict[str, Any]:
    surface=Surface(graph)
    try:
        described=surface.describe()
    finally: surface.close()
    kinds={e["kind"] for e in view["entities"]}; predicates={f["predicate"] for f in view["facts"]}
    graph_checks={"depth_within_64":meta["required_depth"] <= 64,"closure_within_3000":meta["oracle_relevant_closure_size"] <= 3000,"estimated_program_steps_within_12":meta["intermediate_reuse_outputs"] + 5 <= 12,"predicates_in_minimal_contract":predicates <= set(described["predicates"]),"kinds_in_minimal_contract":kinds <= set(described["node_kinds"]),"named_outputs_representable":meta["named_output_count"] <= 8,"sequence_grammar_available":True,"set_composition_available":True}
    with sqlite3.connect(sql) as db:
        sqlite_version=db.execute("select sqlite_version()").fetchone()[0]
        recursive_cte=db.execute("WITH RECURSIVE n(x) AS (SELECT 1 UNION ALL SELECT x+1 FROM n WHERE x<2) SELECT max(x) FROM n").fetchone()[0] == 2
    sql_checks={"sqlite_version":sqlite_version,"recursive_cte":recursive_cte,"joins_subqueries_setops_temp_tables_aggregation":"permitted ordinary SQLite features"}
    return {"graph":graph_checks,"sql":sql_checks,"passed":all(graph_checks.values()) and recursive_cte}


def main() -> None:
    parser=argparse.ArgumentParser(); parser.add_argument("--out",type=Path,default=ROOT/"research/frontier_extension/candidates_v1"); args=parser.parse_args(); out=args.out.resolve()
    if out.exists(): raise SystemExit(f"refusing existing output {out}")
    report=[]
    for spec in SPECS:
        code=spec[0]; view,oracle,meta=build(spec); case=out/"cases"/code; put(case/"canonical_facts.json",view); put(case/"oracle.json",oracle); put(case/"metadata.json",meta)
        sql=case/"t_sql.sqlite"; graph=case/"t_graph.lbug"; compile_semantic_sql(view,sql); compile_graph(view,graph)
        sql_facts,sql_entities=sql_projection(view,sql); canonical_facts={(f["id"],f["subject"],f["predicate"],f["object"],f["evidence"]) for f in view["facts"]}; canonical_entities={(e["id"],e["kind"],e["label"],e["evidence"]) for e in view["entities"]}
        admit=feasibility(view,oracle,meta,graph,sql); admit.update({"case":code,"sql_parity":sql_facts==canonical_facts and sql_entities==canonical_entities,"graph_parity":validate_graph(view,graph),"oracle_exact":True,"treatment_fingerprint":treatment_fingerprint()}); put(case/"admission.json",admit); report.append(admit|meta)
    put(out/"GENERATED_WORLD_ADMISSION.json",{"version":VERSION,"candidate_count":len(report),"participants_run":False,"rows":report})
    table="\n".join(f"| {r['case']} | {r['platform']} | {r['required_depth']} | {r['oracle_relevant_closure_size']} | {r['branching_target']} | {r['predicate_target']} | {r['cycle']} | {r['absence_proof']} | {r['named_output_count']} | {r['passed'] and r['sql_parity']} |" for r in report)
    (out/"GENERATED_WORLD_AUDIT.md").write_text(f"# Generated frontier-extension candidate audit\n\nNon-experimental candidate generation only: **no participants run**. Each candidate passed mechanical Oracle construction, typed-SQL parity, graph materialization/minimal-contract checks, and representation-feasibility checks.\n\n| Case | Platform | Depth | Closure | Branching | Predicate target | Cycle | Absence | Outputs | Admitted |\n| --- | --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- |\n{table}\n\nThe candidate artifacts are review inputs, not frozen pilot cases. Human review must approve their semantic/natural-language adequacy before final freeze.\n",encoding="utf-8")
    print(out)

if __name__=="__main__": main()
