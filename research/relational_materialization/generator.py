"""Paired hidden-world generator for the smallest credible pilot.

The latent model is intentionally small and exact.  H0 and H2 receive the
same facts and task sequence; only their rendering changes.  The evaluator
oracle stays outside each arm workspace.
"""

from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any

from .model import Cell, Heterogeneity, LatentWorld, Novelty, Operation


def make_world(seed: int) -> LatentWorld:
    rng = random.Random(seed)
    resources = tuple(
        {"id": f"resource:{name}", "name": name, "environment": "prod"}
        for name in ("redis-west", "postgres-east", "kafka-core")
    )
    teams = (
        {"id": "team:commerce", "name": "Commerce"},
        {"id": "team:platform", "name": "Platform"},
    )
    services = []
    tests = []
    runbooks = []
    capabilities = ("purchase", "catalogue", "fulfilment", "notifications", "identity", "reporting")
    for index, capability in enumerate(capabilities):
        resource = resources[index % len(resources)]["id"]
        service_id = f"service:{capability}"
        has_test = rng.choice([True, False])
        has_fallback = rng.choice([True, False])
        services.append({
            "id": service_id, "name": f"{capability}-api", "capability": capability,
            "owner": ("team:commerce" if index < 3 else "team:platform"),
            "environment": ("environment:prod" if index % 2 == 0 else "environment:staging"),
            "resource": resource,
        })
        if has_test:
            tests.append({"id": f"test:{capability}-failure", "service": service_id})
        if has_fallback:
            runbooks.append({"id": f"runbook:{capability}-degradation", "capability": capability, "fallback": "degraded-mode"})
    # Guarantee both positive and negative task-specific answers for every seed.
    if not any(s["resource"] == "resource:redis-west" and not any(r["capability"] == s["capability"] for r in runbooks) for s in services):
        runbooks = tuple(r for r in runbooks if r["capability"] != services[0]["capability"])
    return LatentWorld(seed, resources, teams, tuple(services), tuple(tests), tuple(runbooks))


def operations(world: LatentWorld, novelty: Novelty, reuse: int) -> list[Operation]:
    """A coherent prefix workload, not repeated copies of one answer.

    Each query reuses prior world structure while composing a different
    relation. Prefixes (R1/R2/R4/R8) therefore measure cumulative work.
    """
    services = sorted((s for s in world.services if s["resource"] == "resource:redis-west"), key=lambda service: service["id"])
    fallback_capabilities = {r["capability"] for r in world.runbooks if r["fallback"]}
    affected = [s for s in services if s["capability"] not in fallback_capabilities]
    service_ids = tuple(s["id"] for s in services)
    capabilities = tuple(sorted({s["capability"] for s in services}))
    teams = tuple(sorted({s["owner"] for s in services}))
    tests = tuple(sorted(t["id"] for t in world.tests if t["service"] in set(service_ids)))
    affected_capabilities = tuple(sorted({f"capability:{s['capability']}" for s in affected}))
    environments = tuple(sorted({s["environment"] for s in affected if s["environment"] == "environment:prod"}))
    commerce_path = ("answer:yes",) if any(s["owner"] == "team:commerce" for s in services) else ("answer:no",)
    notify_teams = tuple(sorted({s["owner"] for s in affected}))
    sequence = [
        ("services_for_resource", "Which services depend directly on resource redis-west? Return service IDs.", service_ids),
        ("capabilities_for_services", "Which capabilities do the redis-west services provide? Return capability IDs.", tuple(f"capability:{item}" for item in capabilities)),
        ("teams_for_services", "Which teams own the redis-west services? Return team IDs.", teams),
        ("tests_for_services", "Which integration tests cover the redis-west services? Return test IDs.", tests),
        ("affected_capabilities_without_fallback", "Which capabilities of redis-west services lack a documented fallback runbook? Return capability IDs.", affected_capabilities),
        ("production_environments_for_affected", "Which production environments contain redis-west services whose capability lacks a documented fallback? Return environment IDs.", environments),
        ("bounded_path_to_commerce", "Is there a path from redis-west to team:commerce through a dependent service? Return answer:yes or answer:no.", commerce_path),
        ("teams_requiring_migration_notification", "Return the complete set of teams requiring migration notification for redis-west because they own a service whose capability lacks a documented fallback. Return team IDs.", notify_teams),
    ]
    if reuse not in {1, 2, 4, 8}:
        raise ValueError("pilot prefixes must be one of R1, R2, R4, or R8")
    return [Operation(f"op-{index:02d}", prompt, tuple(answer), relation)
            for index, (relation, prompt, answer) in enumerate(sequence[:reuse], start=1)]


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render(world: LatentWorld, target: Path, heterogeneity: Heterogeneity) -> list[Path]:
    """Render only agent-visible sources and return the source paths."""
    sources = target / "sources"
    sources.mkdir(parents=True, exist_ok=True)
    if heterogeneity is Heterogeneity.PRESTRUCTURED:
        path = sources / "world.json"
        _write_json(path, world.to_json())
        return [path]

    services = sources / "services.json"
    _write_json(services, list(world.services))
    with (sources / "teams.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "name"])
        writer.writeheader(); writer.writerows(world.teams)
    with (sources / "resource_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "name", "environment"])
        writer.writeheader(); writer.writerows(world.resources)
    markdown = ["# Service resilience runbooks", ""]
    for runbook in world.runbooks:
        markdown.extend([f"## {runbook['id']}", f"Capability: {runbook['capability']}", f"Fallback: {runbook['fallback']}", ""])
    (sources / "runbooks.md").write_text("\n".join(markdown), encoding="utf-8")
    tests = ["tests:"] + [f"  - id: {item['id']}\n    service: {item['service']}" for item in world.tests]
    (sources / "failure_tests.yaml").write_text("\n".join(tests) + "\n", encoding="utf-8")
    return sorted(sources.iterdir())


def write_case(root: Path, cell: Cell, seed: int) -> Path:
    """Create one runnable case, keeping oracle data in ``evaluator/``."""
    case = root / f"{cell.id}-seed{seed}"
    world = make_world(seed)
    source_paths = render(world, case / "agent", cell.heterogeneity)
    ops = operations(world, cell.novelty, cell.reuse)
    # Evaluator-only relation requirements for the frozen-view experiment.
    # They are derived from latent semantics, never copied into the agent
    # workspace or used to repair an upstream construction.
    from research.frozen_view.core import canonical_from_world
    canonical = canonical_from_world(world.to_json())
    facts = canonical["facts"]
    redis_services = {s["id"] for s in world.services if s["resource"] == "resource:redis-west"}
    capabilities = {f"capability:{s['capability']}" for s in world.services if s["id"] in redis_services}
    fallback_capabilities = {f"capability:{r['capability']}" for r in world.runbooks if r["fallback"]}
    affected_services = {s["id"] for s in world.services if s["id"] in redis_services and f"capability:{s['capability']}" not in fallback_capabilities}

    def fact_ids(predicate: str, *, subjects: set[str] | None = None, objects: set[str] | None = None) -> set[str]:
        return {f["id"] for f in facts if f["predicate"] == predicate and (subjects is None or f["subject"] in subjects) and (objects is None or f["object"] in objects)}

    dependencies = fact_ids("depends_on", subjects=redis_services, objects={"resource:redis-west"})
    provides = fact_ids("provides", subjects=redis_services)
    owners = fact_ids("owned_by", subjects=redis_services)
    tests = fact_ids("covers", objects=redis_services)
    runbooks = fact_ids("covers_capability", objects=capabilities)
    affected_deployments = fact_ids("deployed_in", subjects=affected_services)
    affected_owners = fact_ids("owned_by", subjects=affected_services)
    requirements = [
        dependencies,
        dependencies | provides,
        dependencies | owners,
        dependencies | tests,
        dependencies | provides | runbooks,
        dependencies | provides | runbooks | affected_deployments,
        dependencies | owners,
        dependencies | provides | runbooks | affected_owners,
    ]
    # The workload describes requests only.  Answer IDs are evaluator-only;
    # leaking them here would turn every arm into an oracle lookup.
    _write_json(case / "agent" / "workload.json", {
        "cell": cell.id,
        "operations": [{"id": op.id, "prompt": op.prompt, "relation": op.relation} for op in ops],
    })
    (case / "evaluator").mkdir(parents=True, exist_ok=True)
    _write_json(case / "evaluator" / "oracle.json", {
        "cell": cell.id, "seed": seed, "operations": [op.to_json() for op in ops],
        "source_files": [str(path.relative_to(case / "agent")) for path in source_paths],
        "oracle_relation_ids": sorted(set().union(*requirements[:len(ops)])),
        "oracle_relation_requirements": [
            {"operation_id": op.id, "relation_ids": sorted(requirements[index])}
            for index, op in enumerate(ops)
        ],
    })
    return case
