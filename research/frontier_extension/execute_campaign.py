"""Seal, preflight, and execute the approved frozen frontier-extension campaign.

This is experiment infrastructure only.  It never mutates a candidate artifact,
projection, oracle, grader, product surface, or frozen graph-treatment adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from research.abstraction_frontier.campaign import GRAPH_ACCESS, SQL_AUDIT, graph_policy, sql_policy
from research.abstraction_frontier.treatment import treatment_fingerprint
from research.frontier_extension.prompt_consistency import output_consistency


ROOT = Path(__file__).resolve().parents[2]
CANDIDATES = ROOT / "research/frontier_extension/candidates_v5_final_review"
PROTOCOL = "frozen-frontier-extension-v1"
DECLARED_MODEL = "Composer 2.5"
MODEL_SELECTOR = "composer-2.5"
MODEL_COMMAND = ["cursor-agent", "-p", "--output-format", "stream-json", "--model", MODEL_SELECTOR, "--force"]
TIMEOUT_SECONDS = 240
ARMS = ("T_SQL", "T_GRAPH")


def canonical(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(value), encoding="utf-8")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_output(args: list[str]) -> str:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False).stdout.strip()


def runtime_environment() -> dict[str, Any]:
    status = command_output(["git", "status", "--porcelain=v1"])
    diff = subprocess.run(["git", "diff", "--binary", "HEAD"], cwd=ROOT, text=True, capture_output=True, check=False).stdout
    with sqlite3.connect(":memory:") as db:
        sqlite_version = db.execute("select sqlite_version()").fetchone()[0]
    return {
        "product_commit": command_output(["git", "rev-parse", "HEAD"]),
        "product_commit_short": command_output(["git", "rev-parse", "--short", "HEAD"]),
        "working_tree_status": status.splitlines(),
        "working_tree_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
        "python_executable": sys.executable,
        "python_version": sys.version,
        "platform": platform.platform(),
        "cursor_agent_version": command_output(["cursor-agent", "--version"]),
        "sqlite_version": sqlite_version,
    }


def case_paths(case: str) -> dict[str, Path]:
    base = CANDIDATES / "cases" / case
    return {
        "canonical": base / "canonical_facts.json",
        "oracle": base / "oracle.json",
        "metadata": base / "metadata.json",
        "admission": base / "admission.json",
        "sql": base / "t_sql.sqlite",
        "graph": base / "t_graph.lbug",
        "graph_metadata": base / "t_graph.lbug.metadata.json",
    }


def collect_cases() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for directory in sorted((CANDIDATES / "cases").iterdir()):
        paths = case_paths(directory.name)
        metadata, oracle, admission = (load(paths[key]) for key in ("metadata", "oracle", "admission"))
        contract = output_consistency(metadata, oracle)
        grader = oracle.get("grader_expected_outputs", {})
        requested_names = set(metadata.get("participant_requested_outputs", []))
        exact_named_set_grading = (
            len(requested_names) == len(metadata.get("participant_requested_outputs", []))
            and requested_names == set(oracle.get("answers", {})) == set(grader)
            and oracle.get("answers") == grader
        )
        if not admission.get("passed") or not all(contract.values()) or not exact_named_set_grading:
            raise RuntimeError(f"candidate {directory.name} failed frozen admission/grader consistency")
        rows.append({
            "case_id": directory.name,
            "prompt": metadata["prompt"],
            "output_names": list(metadata["participant_requested_outputs"]),
            "expected": oracle["answers"],
            "grader_expected": grader,
            "metadata": metadata,
            "paths": paths,
        })
    if [row["case_id"] for row in rows] != [f"FX{i:02d}" for i in range(1, 15)]:
        raise RuntimeError("candidate case order is not the approved FX01–FX14 sequence")
    return rows


def case_integrity(case: dict[str, Any]) -> dict[str, str]:
    return {
        "canonical_facts_sha256": sha256(case["paths"]["canonical"]),
        "oracle_sha256": sha256(case["paths"]["oracle"]),
        "sql_projection_sha256": sha256(case["paths"]["sql"]),
        "graph_projection_sha256": sha256(case["paths"]["graph"]),
        "participant_prompt_sha256": hashlib.sha256(case["prompt"].encode("utf-8")).hexdigest(),
    }


def graph_adapter_integrity() -> dict[str, str]:
    frozen = load(ROOT / "research/abstraction_frontier/FROZEN_GRAPH_TREATMENT_CONFORMANCE_V1.json")
    actual = hashlib.sha256(GRAPH_ACCESS.encode("utf-8")).hexdigest()
    if actual != frozen["adapter_source_sha256"] or treatment_fingerprint() != frozen["treatment_fingerprint"]:
        raise RuntimeError("frozen graph adapter/policy no longer matches its conformance record")
    return {
        "treatment_version": frozen["treatment_version"],
        "treatment_fingerprint": frozen["treatment_fingerprint"],
        "adapter_source_sha256": actual,
    }


def schedule(cases: list[dict[str, Any]]) -> list[dict[str, str]]:
    # Alternating first arm balances the serial order while preserving each pair.
    result: list[dict[str, str]] = []
    for index, case in enumerate(cases):
        order = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
        for pair_position, arm in enumerate(order, 1):
            result.append({"case_id": case["case_id"], "arm": arm, "pair_position": str(pair_position)})
    return result


def seal(run_root: Path) -> dict[str, Any]:
    if run_root.exists():
        raise SystemExit(f"refusing existing campaign root: {run_root}")
    cases = collect_cases()
    adapter = graph_adapter_integrity()
    environment = runtime_environment()
    manifest = {
        "protocol_version": PROTOCOL,
        "status": "sealed_pre_execution",
        "candidate_source": str(CANDIDATES.relative_to(ROOT)),
        "candidate_count": len(cases),
        "episode_count": len(cases) * len(ARMS),
        "arms": list(ARMS),
        "fixed_case_order": [case["case_id"] for case in cases],
        "fixed_paired_arm_order": schedule(cases),
        "retry_policy": "no within-episode automatic retries",
        "declared_model": DECLARED_MODEL,
        "model_selector": MODEL_SELECTOR,
        "model_command": MODEL_COMMAND,
        "model_budget": {"token_budget": "not exposed by cursor-agent CLI", "timeout_seconds_per_episode": TIMEOUT_SECONDS},
        "execution_harness_sha256": sha256(Path(__file__)),
        "runtime_environment": environment,
        "graph_treatment": adapter,
        "exact_named_set_grading": {
            "required": True,
            "rule": "every requested named output must equal its corresponding oracle/grader set; union-only scoring is invalid",
        },
        "cases": [{
            "case_id": case["case_id"], "prompt": case["prompt"], "output_names": case["output_names"],
            "integrity": case_integrity(case),
        } for case in cases],
    }
    write_json(run_root / "CAMPAIGN_MANIFEST.json", manifest)
    manifest_hash = sha256(run_root / "CAMPAIGN_MANIFEST.json")
    seal_record = {"manifest_sha256": manifest_hash, "sealed": True, "workspace_creation_before_seal": False}
    write_json(run_root / "MANIFEST_SEALED.json", seal_record)
    (run_root / "CAMPAIGN_MANIFEST.json").chmod(0o444)
    write_json(run_root / "FINAL_GRADER_CONSISTENCY.json", {
        "passed": True,
        "per_case": [{"case_id": case["case_id"], "requested": case["output_names"],
                      "oracle": list(case["expected"]), "grader": list(case["grader_expected"]),
                      "exact_named_set_grading": True} for case in cases],
    })
    return manifest


def verify_seal(run_root: Path) -> dict[str, Any]:
    manifest_path, seal_path = run_root / "CAMPAIGN_MANIFEST.json", run_root / "MANIFEST_SEALED.json"
    if not manifest_path.exists() or not seal_path.exists():
        raise RuntimeError("campaign manifest is not sealed")
    manifest, seal_record = load(manifest_path), load(seal_path)
    if sha256(manifest_path) != seal_record.get("manifest_sha256"):
        raise RuntimeError("sealed manifest hash mismatch")
    current_cases = {case["case_id"]: case for case in collect_cases()}
    for frozen in manifest["cases"]:
        current = current_cases.get(frozen["case_id"])
        if current is None or case_integrity(current) != frozen["integrity"] or current["prompt"] != frozen["prompt"]:
            raise RuntimeError(f"sealed candidate drift: {frozen['case_id']}")
    if graph_adapter_integrity() != manifest["graph_treatment"]:
        raise RuntimeError("sealed graph treatment drift")
    now = runtime_environment()
    expected = manifest["runtime_environment"]
    constancy_keys = ("product_commit", "working_tree_diff_sha256", "python_executable", "python_version", "cursor_agent_version", "sqlite_version")
    changed = {key: {"sealed": expected[key], "current": now[key]} for key in constancy_keys if expected[key] != now[key]}
    if changed:
        raise RuntimeError(f"sealed execution environment drift: {changed}")
    return manifest


def quota_signal(text: str) -> bool:
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        candidates: list[Any] = [
            event.get("status"),
            event.get("code"),
            event.get("message"),
            event.get("reason"),
        ]
        nested = event.get("error")
        if isinstance(nested, dict):
            candidates.extend([
                nested.get("status"),
                nested.get("code"),
                nested.get("message"),
                nested.get("reason"),
            ])
        for candidate in candidates:
            if candidate is None:
                continue
            normalized = str(candidate).lower()
            if any(token in normalized for token in ("rate limit", "quota", "too many requests")) or "429" in normalized:
                return True
    return False


def stream_events(stdout: str, stderr: str) -> tuple[list[dict[str, Any]], str | None, bool, dict[str, Any] | None]:
    events: list[dict[str, Any]] = []
    identity: str | None = None
    usage: dict[str, Any] | None = None
    for line in (stdout + "\n" + stderr).splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        events.append(event)
        if event.get("type") == "system" and event.get("subtype") == "init":
            identity = str(event.get("model") or "")
        if event.get("type") in {"usage", "token_usage"}:
            usage = event
    return events, identity, quota_signal(stdout + "\n" + stderr), usage


def result_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        output = []
        for key, item in value.items():
            if key == "result":
                output.append(item)
            output.extend(result_values(item))
        return output
    if isinstance(value, list):
        return [nested for item in value for nested in result_values(item)]
    return []


def payload_accounting(events: list[dict[str, Any]]) -> dict[str, Any]:
    total = semantic = answers = 0
    entity_count = relation_count = path_count = 0
    for event in events:
        if event.get("type") != "tool_call" or event.get("subtype") != "completed":
            continue
        for result in result_values(event.get("tool_call", {})):
            raw = json.dumps(result, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
            total += len(raw)
            decoded: Any = result
            if isinstance(result, str):
                try:
                    decoded = json.loads(result)
                except ValueError:
                    decoded = result
            if isinstance(decoded, dict) and ("answers" in decoded or "outcome" in decoded or "nodes" in decoded or "rows" in decoded):
                body = json.dumps(decoded, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
                semantic += len(body)
                if isinstance(decoded.get("answers"), dict):
                    answer_payload = json.dumps(decoded["answers"], sort_keys=True, separators=(",", ":")).encode("utf-8")
                    answers += len(answer_payload)
                entity_count += len(decoded.get("nodes") or decoded.get("entities") or [])
                relation_count += len(decoded.get("edges") or decoded.get("relations") or [])
                path_count += len(decoded.get("paths") or [])
            else:
                semantic += len(raw)
    return {
        "total_model_visible_bytes": total,
        "semantic_result_bytes": semantic,
        "answer_bytes": answers,
        "wrapper_or_receipt_bytes": max(total - semantic, 0),
        "model_visible_entity_count": entity_count,
        "model_visible_relation_count": relation_count,
        "model_visible_path_count": path_count,
        "method": "UTF-8 bytes of every completed Cursor tool-result payload; decoded graph/structured result components are semantic data, with remaining bytes wrapper/receipt overhead",
    }


def prepare_workspace(run_root: Path, case: dict[str, Any], arm: str) -> tuple[Path, Path, Path, Path]:
    verify_seal(run_root)  # Enforces the no-workspace-before-seal boundary.
    root = run_root / "executions" / case["case_id"] / arm
    workspace = root / "workspace"
    workspace.mkdir(parents=True, exist_ok=False)
    sql_audit, graph_audit = workspace / "sql_queries.jsonl", workspace / "graph_operations.jsonl"
    workload = {
        "case_id": case["case_id"], "engineering_task": case["prompt"],
        "answer_contract": "Write $FX_RESPONSE as JSON: {answers:{answer_name:[stable_id,...]}}. Include every requested named answer set, no unrequested answer names, and no explanation.",
        "answer_names": case["output_names"],
    }
    write_json(workspace / "workload.json", workload)
    if arm == "T_SQL":
        shutil.copy2(case["paths"]["sql"], workspace / "view.sqlite")
        (workspace / "access-policy.md").write_text(sql_policy(), encoding="utf-8")
        (workspace / "sitecustomize.py").write_text(SQL_AUDIT, encoding="utf-8")
    else:
        shutil.copy2(case["paths"]["graph"], workspace / "view.lbug")
        shutil.copy2(case["paths"]["graph_metadata"], Path(str(workspace / "view.lbug") + ".metadata.json"))
        (workspace / "access-policy.md").write_text(graph_policy(), encoding="utf-8")
        client = workspace / "graphauthor_access.py"
        client.write_text(GRAPH_ACCESS, encoding="utf-8")
        client.chmod(0o755)
    return root, workspace, sql_audit, graph_audit


def score(expected: dict[str, list[str]], output_names: list[str], response: dict[str, Any]) -> dict[str, Any]:
    answers = response.get("answers") if isinstance(response, dict) else None
    actual = answers if isinstance(answers, dict) else {}
    names_exact = list(actual) == output_names
    per_name = {
        name: sorted(set(map(str, actual.get(name, [])))) == sorted(expected[name]) if isinstance(actual.get(name, []), list) else False
        for name in output_names
    }
    return {"exact_named_answer_sets": per_name, "answer_names_exact": names_exact,
            "exact_correct": names_exact and all(per_name.values()), "expected": expected, "actual": actual}


def read_events(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.exists() else []


def run_episode(run_root: Path, case: dict[str, Any], arm: str, manifest: dict[str, Any]) -> dict[str, Any]:
    root, workspace, sql_audit, graph_audit = prepare_workspace(run_root, case, arm)
    response = root / "response.json"
    prompt = "Work only in the workspace. Read workload.json and access-policy.md. Complete the task and write the required JSON to $FX_RESPONSE. Do not inspect parent directories, evaluator files, raw sources, or the internet."
    env = os.environ | {
        "FX_RESPONSE": str(response), "AF_SQL_AUDIT": str(sql_audit), "AF_GRAPH_AUDIT": str(graph_audit),
        "PYTHONPATH": str(workspace) + os.pathsep + str(ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""), "NO_PROXY": "*",
    }
    started = time.perf_counter()
    process = subprocess.Popen(MODEL_COMMAND + [prompt], cwd=workspace, env=env, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
    timed_out = False
    while process.poll() is None and time.perf_counter() - started < TIMEOUT_SECONDS:
        time.sleep(0.2)
    if process.poll() is None:
        os.killpg(process.pid, signal.SIGTERM)
        timed_out = True
    stdout, stderr = process.communicate()
    elapsed = time.perf_counter() - started
    try:
        response_payload = json.loads(response.read_text(encoding="utf-8"))
        response_valid = isinstance(response_payload, dict)
    except (OSError, ValueError):
        response_payload, response_valid = {}, False
    events, identity, quota, usage = stream_events(stdout, stderr)
    sql_events, graph_events = read_events(sql_audit), read_events(graph_audit)
    operation_events = sql_events if arm == "T_SQL" else graph_events
    errors = [event for event in operation_events if str(event.get("event", "")).endswith(("failure", "rejected"))]
    record = {
        "protocol_version": PROTOCOL, "case_id": case["case_id"], "arm": arm,
        "declared_model": DECLARED_MODEL, "reported_model_identifier": identity,
        "model_identity_matches_manifest": identity == manifest["declared_model"],
        "returncode": process.returncode, "timed_out": timed_out,
        "execution_status": "completed" if response_valid and not timed_out else "timeout" if timed_out else "invalid_or_missing_response",
        "valid_execution": response_valid and not timed_out,
        "wall_seconds": elapsed, "score": score(case["expected"], case["output_names"], response_payload),
        "model_environment_interaction_count": sum(event.get("type") == "tool_call" and event.get("subtype") == "started" for event in events),
        "tool_calls": [event for event in events if event.get("type") == "tool_call"],
        "sql_queries": sql_events, "graph_operations": graph_events,
        "operation_ordering": sorted(sql_events + graph_events, key=lambda event: event.get("order", 0)),
        "payload_accounting": payload_accounting(events), "participant_facing_errors": errors,
        "participant_facing_error_count": len(errors), "raw_source_fallback_count": 0,
        "quota_or_rate_limit_signal": quota, "model_usage": usage, "stdout": stdout, "stderr": stderr,
    }
    write_json(root / "record.json", record)
    return record


def preflight(run_root: Path) -> dict[str, Any]:
    manifest = verify_seal(run_root)
    pre = run_root / "preflight"
    if pre.exists():
        raise SystemExit("preflight already exists")
    pre.mkdir()
    model_dir = pre / "model"; model_dir.mkdir()
    proc = subprocess.run(MODEL_COMMAND + ["Reply with exactly: preflight-ready"], cwd=model_dir, text=True, capture_output=True, timeout=TIMEOUT_SECONDS)
    model_events, model_identity, quota, _ = stream_events(proc.stdout, proc.stderr)
    case = collect_cases()[0]
    sql_dir = pre / "sql"; sql_dir.mkdir(); shutil.copy2(case["paths"]["sql"], sql_dir / "view.sqlite")
    (sql_dir / "sitecustomize.py").write_text(SQL_AUDIT, encoding="utf-8")
    sql_audit = sql_dir / "sql.jsonl"
    sql = subprocess.run([sys.executable, "-c", "import sqlite3; print(sqlite3.connect('view.sqlite').execute(\"select count(*) from sqlite_master\").fetchone()[0])"], cwd=sql_dir, text=True, capture_output=True, env=os.environ | {"AF_SQL_AUDIT": str(sql_audit), "PYTHONPATH": str(sql_dir) + os.pathsep + str(ROOT)})
    graph_dir = pre / "graph"; graph_dir.mkdir(); shutil.copy2(case["paths"]["graph"], graph_dir / "view.lbug")
    shutil.copy2(case["paths"]["graph_metadata"], Path(str(graph_dir / "view.lbug") + ".metadata.json"))
    client = graph_dir / "graphauthor_access.py"; client.write_text(GRAPH_ACCESS, encoding="utf-8"); client.chmod(0o755)
    graph_audit = graph_dir / "graph.jsonl"; graph_env = os.environ | {"AF_GRAPH_AUDIT": str(graph_audit), "PYTHONPATH": str(ROOT)}
    describe = subprocess.run([sys.executable, str(client), "describe", "{}"], cwd=graph_dir, text=True, capture_output=True, env=graph_env)
    lookup = subprocess.run([sys.executable, str(client), "lookup", json.dumps({"references": [case["metadata"]["neutral_program"]["seed"]]})], cwd=graph_dir, text=True, capture_output=True, env=graph_env)
    excluded = subprocess.run([sys.executable, str(client), "run_ephemeral_traversal", json.dumps({"program": {"steps": [{"op": "search", "query": "forbidden"}]}})], cwd=graph_dir, text=True, capture_output=True, env=graph_env)
    graph_log = read_events(graph_audit)
    receipt = {
        "non_experimental": True, "manifest_sha256": sha256(run_root / "CAMPAIGN_MANIFEST.json"),
        "model_callable": proc.returncode == 0, "reported_model_identifier": model_identity,
        "reported_model_matches_declared": model_identity == manifest["declared_model"],
        "experiment_server_identity": {"cursor_agent_version": manifest["runtime_environment"]["cursor_agent_version"], "graph_describe_returncode": describe.returncode},
        "sql_treatment_callable": sql.returncode == 0, "graph_treatment_callable": describe.returncode == 0 and lookup.returncode == 0,
        "candidate_opened_without_oracle": sql.returncode == 0 and describe.returncode == 0 and lookup.returncode == 0,
        "treatment_matches_manifest": graph_adapter_integrity() == manifest["graph_treatment"],
        "excluded_operation_rejected": excluded.returncode != 0 and any(event.get("before_execution") for event in graph_log),
        "logging_endpoints_work": sql_audit.exists() and graph_audit.exists(),
        "quota_detector_operational": quota_signal(json.dumps({"error": {"status": 429, "message": "quota and rate limit detector fixture"}})) and not quota,
        "details": {"model_returncode": proc.returncode, "sql_stderr": sql.stderr, "graph_stderr": describe.stderr, "excluded_stderr": excluded.stderr},
    }
    receipt["passed"] = all(value for key, value in receipt.items() if key not in {"non_experimental", "manifest_sha256", "details", "reported_model_identifier", "experiment_server_identity", "passed"})
    write_json(pre / "PREFLIGHT_RECEIPT.json", receipt)
    if not receipt["passed"]:
        raise RuntimeError("preflight failed; campaign will not start")
    return receipt


def report(run_root: Path, records: list[dict[str, Any]], aborted: str | None = None) -> None:
    manifest = load(run_root / "CAMPAIGN_MANIFEST.json")
    expected_cells = len(manifest["fixed_paired_arm_order"])
    constancy = all(record["model_identity_matches_manifest"] for record in records)
    complete = len(records) == expected_cells and aborted is None
    valid = complete and constancy
    rows = "\n".join(
        f"| {record['case_id']} | {record['arm']} | {record['valid_execution']} | {record['score']['exact_correct']} | {record['model_environment_interaction_count']} | {record['payload_accounting']['total_model_visible_bytes']} | {record['participant_facing_error_count']} | {record['wall_seconds']:.2f} |"
        for record in records
    )
    summary = {
        "campaign_valid": valid, "campaign_complete": complete, "model_environment_constant": constancy,
        "expected_cells": expected_cells, "completed_cells": len(records), "abort_reason": aborted,
        "records": records,
    }
    write_json(run_root / "CAMPAIGN_RESULTS.json", summary)
    text = f"""# Frontier-extension execution report — no frontier interpretation

| Check | Value |
| --- | --- |
| Campaign validity | `{valid}` |
| Model/environment constancy | `{constancy}` |
| Completion | `{len(records)}/{expected_cells}` |
| Declared/reported model | `{DECLARED_MODEL}` |
| Abort reason | `{aborted or 'none'}` |

| Case | Arm | Valid execution | Exact named-set correct | Interactions | Model-visible bytes | Participant errors | Wall seconds |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
{rows}

This report intentionally contains no SQL-versus-graph frontier conclusion.
The sealed records retain SQL statement/row telemetry and graph-operation,
program, result-mode, and evidence telemetry for the preregistered analysis.
"""
    (run_root / "EXECUTION_REPORT.md").write_text(text, encoding="utf-8")


def execute(run_root: Path) -> None:
    manifest = verify_seal(run_root)
    receipt = load(run_root / "preflight/PREFLIGHT_RECEIPT.json")
    if not receipt.get("passed"):
        raise RuntimeError("cannot execute without a passing preflight")
    cases = {case["case_id"]: case for case in collect_cases()}
    records: list[dict[str, Any]] = []
    abort_reason: str | None = None
    for cell in manifest["fixed_paired_arm_order"]:
        record = run_episode(run_root, cases[cell["case_id"]], cell["arm"], manifest)
        records.append(record)
        if not record["model_identity_matches_manifest"]:
            abort_reason = f"model identity drift in {record['case_id']}/{record['arm']}"
        elif record["quota_or_rate_limit_signal"]:
            abort_reason = f"quota/rate-limit dependency failure in {record['case_id']}/{record['arm']}"
        if abort_reason:
            write_json(run_root / "CAMPAIGN_ABORT.json", {"reason": abort_reason, "completed_cells": len(records)})
            break
    report(run_root, records, abort_reason)
    if abort_reason:
        raise SystemExit("campaign aborted and marked invalid")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=Path, default=ROOT / "research/frontier_extension/runs/fx_campaign_20260830")
    parser.add_argument("--freeze", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if sum((args.freeze, args.preflight, args.execute)) != 1:
        raise SystemExit("choose exactly one of --freeze, --preflight, or --execute")
    root = args.run_root.resolve()
    if args.freeze:
        seal(root)
    elif args.preflight:
        preflight(root)
    else:
        execute(root)


if __name__ == "__main__":
    main()
