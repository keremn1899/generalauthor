"""Deterministic smoke-test participant used only to validate runner plumbing.

The pilot evaluator owns the oracle; this participant instead derives answers
from visible source files. It makes no claim about agent performance.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path


def _world(root: Path) -> dict:
    combined = root / "sources" / "world.json"
    if combined.exists():
        return json.loads(combined.read_text())
    services = json.loads((root / "sources" / "services.json").read_text())
    runbook_text = (root / "sources" / "runbooks.md").read_text()
    runbooks = []
    for section in runbook_text.split("## ")[1:]:
        lines = section.splitlines()
        values = {line.split(": ", 1)[0].lower(): line.split(": ", 1)[1] for line in lines[1:] if ": " in line}
        runbooks.append({"id": lines[0], "capability": values["capability"], "fallback": values["fallback"]})
    tests = []
    for section in (root / "sources" / "failure_tests.yaml").read_text().split("  - id: ")[1:]:
        identifier, service_line = section.splitlines()[:2]
        tests.append({"id": identifier, "service": service_line.split(": ", 1)[1]})
    return {"services": services, "runbooks": runbooks, "tests": tests}


def main() -> None:
    root = Path(os.environ["RM_AGENT_WORKSPACE"])
    workload = json.loads((root / "workload.json").read_text())
    world = _world(root)
    fallback = {r["capability"] for r in world["runbooks"] if r["fallback"]}
    services = [s for s in world["services"] if s["resource"] == "resource:redis-west"]
    affected = [s for s in services if s["capability"] not in fallback]
    values = {
        "services_for_resource": [s["id"] for s in services],
        "capabilities_for_services": [f"capability:{item}" for item in sorted({s["capability"] for s in services})],
        "teams_for_services": sorted({s["owner"] for s in services}),
        "tests_for_services": sorted(t["id"] for t in world["tests"] if t["service"] in {s["id"] for s in services}),
        "affected_capabilities_without_fallback": [f"capability:{item}" for item in sorted({s["capability"] for s in affected})],
        "production_environments_for_affected": sorted({s["environment"] for s in affected if s["environment"] == "environment:prod"}),
        "bounded_path_to_commerce": ["answer:yes" if any(s["owner"] == "team:commerce" for s in services) else "answer:no"],
        "teams_requiring_migration_notification": sorted({s["owner"] for s in affected}),
    }
    answers = []
    for operation in workload["operations"]:
        answers.append({"operation_id": operation["id"], "answer_ids": values[operation["relation"]]})
    arm = os.environ["RM_ARM"]
    artifacts = {"representation_path": "reference-derived"}
    if arm == "B":
        store = root / "relation_store.sqlite"  # Runner creates its required schema before timing.
        artifacts["representation_path"] = store.name
    elif arm == "C":
        workbook = root / "workbook"
        (workbook / "out").mkdir(parents=True, exist_ok=True)
        (workbook / "out" / "encoding.json").write_text('{"nodes": [], "edges": []}\n')
        artifacts["graphauthor_workbook"] = workbook.name
    response = {"answers": answers, "artifacts": artifacts}
    Path(os.environ["RM_RESPONSE_PATH"]).write_text(json.dumps(response), encoding="utf-8")


if __name__ == "__main__":
    main()
