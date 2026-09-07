"""Run the E2E programmability campaign except fresh-agent LLM calls."""

from __future__ import annotations

import csv
import json
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.compact_header import (
    write_header,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.diffs import diff_states, write_diff
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.freeze import freeze_inputs
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.isolation import (
    new_live_workspace,
    preflight_isolation,
    remove_live_workspace,
    run_isolated,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.leakage import audit_consumers
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.materialize import (
    materialize_all,
    seed_compile_workspace,
    sha256_file,
)
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    CONSUMERS,
    DIFFS,
    FAILURE,
    ISOLATED,
    MANUAL,
    OUTPUTS,
    ROOT,
    RUNS,
    STATES,
    STATES_USED,
    T5_CONSTRUCTION,
)
from research.semantic_integration.domains.bom.llm_world_programming_v2.isolation import host_python


def _copy_isolated_state(state_id: str) -> Path:
    dest = ISOLATED / state_id
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copytree(STATES / state_id / "accepted", dest / "accepted")
    shutil.copy2(STATES / state_id / "compact_header.md", dest / "compact_header.md")
    shutil.copytree(CONSUMERS, dest / "consumers")
    (dest / "README.md").write_text(
        "Source-free consumer workspace. Accepted World + consumers only. No CSV/PDF corpus.\n",
        encoding="utf-8",
    )
    return dest


def _live_consumer_workspace(state_id: str) -> Path:
    live = new_live_workspace()
    src = ISOLATED / state_id
    shutil.copytree(src / "accepted", live / "accepted")
    shutil.copy2(src / "compact_header.md", live / "compact_header.md")
    shutil.copytree(src / "consumers", live / "consumers")
    shutil.copy2(src / "README.md", live / "README.md")
    return live


def _run_consumer_isolated(state_id: str, output_dir: Path) -> dict:
    workspace_copy = _copy_isolated_state(state_id)
    native = [
        p
        for p in workspace_copy.rglob("*")
        if p.suffix.lower() in {".csv", ".pdf"} or p.name.endswith("final_permit.txt")
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    live = _live_consumer_workspace(state_id)
    try:
        py = live / "consumers" / "python" / "monitoring_analysis.py"
        sql = live / "consumers" / "sql" / "monitoring_analysis.sql"
        world = live / "accepted" / "world.sqlite"
        out_live = live / "output"
        argv = [host_python(), str(py), str(world), str(out_live), str(sql)]
        preflight_isolation(live)
        completed = run_isolated(live, argv, timeout=120)
        if completed.returncode != 0:
            raise RuntimeError(
                f"WORLD_ONLY_CONSUMPTION_FAILED {state_id}: {completed.stdout[-1500:]}\n{completed.stderr[-1500:]}"
            )
        shutil.copytree(out_live, output_dir, dirs_exist_ok=True)
        summary = json.loads((output_dir / "summary.json").read_text(encoding="utf-8"))
        summary["native_files_in_workspace"] = [str(p.relative_to(workspace_copy)) for p in native]
        summary["world_only"] = len(native) == 0
        summary["consumer_returncode"] = completed.returncode
        summary["live_workspace"] = str(live)
        return summary
    finally:
        remove_live_workspace(live)


def _failed_candidate(accepted_sqlite: Path, before_output: Path) -> dict:
    FAILURE.mkdir(parents=True, exist_ok=True)
    before_world = sha256_file(accepted_sqlite)
    before_csv = sha256_file(before_output / "monitoring_analysis.csv")
    live = new_live_workspace()
    try:
        seed_compile_workspace(live, T5_CONSTRUCTION)
        (live / "construction.py").write_text("this is not valid python $$$\n", encoding="utf-8")
        completed = subprocess.run(
            [sys.executable, str(live / "_run_construction.py")],
            cwd=live,
            text=True,
            capture_output=True,
            check=False,
        )
        after_world = sha256_file(accepted_sqlite)
        after_csv = sha256_file(before_output / "monitoring_analysis.csv")
        payload = {
            "FAILED_CANDIDATE_PRESERVES_ACCEPTED": before_world == after_world,
            "FAILED_CANDIDATE_PRESERVES_APPLICATION_OUTPUT": before_csv == after_csv,
            "before_world_sha256": before_world,
            "after_world_sha256": after_world,
            "before_csv_sha256": before_csv,
            "after_csv_sha256": after_csv,
            "compile_returncode": completed.returncode,
            "compile_ok_expected_false": completed.returncode != 0,
        }
    finally:
        remove_live_workspace(live)
    (FAILURE / "result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (FAILURE / "README.md").write_text(
        "Deliberately invalid construction.py compiled in a disposable directory. "
        "Accepted State C World and application output were not write targets.\n",
        encoding="utf-8",
    )
    return payload


def _reopen(state_id: str, original_csv: Path) -> dict:
    live = _live_consumer_workspace(state_id)
    try:
        py = live / "consumers" / "python" / "monitoring_analysis.py"
        sql = live / "consumers" / "sql" / "monitoring_analysis.sql"
        world = live / "accepted" / "world.sqlite"
        out_live = live / "output"
        argv = [host_python(), str(py), str(world), str(out_live), str(sql)]
        completed = run_isolated(live, argv, timeout=120)
        if completed.returncode != 0:
            raise RuntimeError(f"reopen failed: {completed.stderr[-1500:]}")
        match = sha256_file(original_csv) == sha256_file(out_live / "monitoring_analysis.csv")
        return {
            "REOPEN_WITHOUT_RECONSTRUCTION": match,
            "original_sha256": sha256_file(original_csv),
            "reopen_sha256": sha256_file(out_live / "monitoring_analysis.csv"),
        }
    finally:
        remove_live_workspace(live)


def _write_traces() -> list[dict]:
    traces_dir = MANUAL / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    a = {r["application_key"]: r for r in csv.DictReader((OUTPUTS / "state_a" / "monitoring_analysis.csv").open())}
    b = {r["application_key"]: r for r in csv.DictReader((OUTPUTS / "state_b" / "monitoring_analysis.csv").open())}
    c = {r["application_key"]: r for r in csv.DictReader((OUTPUTS / "state_c" / "monitoring_analysis.csv").open())}
    picked: list[tuple[str, str, dict, dict]] = []

    def take(label: str, key: str, before: dict, after: dict) -> None:
        if key and len(picked) < 12:
            picked.append((label, key, before, after))

    for key, row in b.items():
        if row.get("monitoring_status") == "UNRESOLVED_FACTUAL" and a.get(key, {}).get("monitoring_status") == "UNRESOLVED_SEMANTIC":
            take("when_discharging_sharpened", key, a[key], row)
            break
    for key, row in c.items():
        if row.get("comparison_status") in {"PASS", "FAIL"} and a.get(key, {}).get("comparison_status") != row.get("comparison_status"):
            take("pass_fail_classified", key, b.get(key, a.get(key, {})), row)
            if len([p for p in picked if p[0] == "pass_fail_classified"]) >= 2:
                break
    for key, row in c.items():
        if row.get("nodi_code") == "C" and "nodi_code_semantics" in (row.get("unresolved_reason") or ""):
            take("nodi_c_unresolved", key, a[key], row)
            break
    for key, row in c.items():
        if row.get("nodi_code") == "9" and "nodi_code_semantics" in (row.get("unresolved_reason") or ""):
            take("nodi_9_unresolved", key, a[key], row)
            break
    for key, row in c.items():
        if a.get(key) == row and row.get("comparison_status") in {"EXCEEDANCE", "WITHIN_LIMIT"}:
            take("unaffected_numeric_control", key, a[key], row)
            break
    for key, row in b.items():
        if row.get("monitoring_status") == a.get(key, {}).get("monitoring_status") and row.get("comparison_status") in {"EXCEEDANCE", "WITHIN_LIMIT"}:
            take("unaffected_after_when_discharging", key, a[key], row)
            if len([p for p in picked if p[0].startswith("unaffected")]) >= 3:
                break

    records = []
    for i, (label, key, before, after) in enumerate(picked, 1):
        conn = sqlite3.connect(STATES / "state_c" / "accepted" / "world.sqlite")
        conn.row_factory = sqlite3.Row
        try:
            mlp = conn.execute(
                "SELECT * FROM measurement_limit_pair WHERE measurement = ?", (key,)
            ).fetchone()
            holes = conn.execute(
                "SELECT requirement, failure_kind, subject_json, grounding_json FROM _hole WHERE subject_json LIKE ?",
                (f"%{key}%",),
            ).fetchall()
            origins = json.loads((STATES / "state_c" / "accepted" / "world.sqlite.origins.json").read_text())
        finally:
            conn.close()
        rec = {
            "id": f"T{i:02d}",
            "label": label,
            "application_key": key,
            "before": before,
            "after": after,
            "world_tuple": dict(mlp) if mlp else {},
            "holes": [dict(h) for h in holes],
            "origins_pointer": origins.get("proposals"),
            "traceable": bool(mlp),
        }
        records.append(rec)
        md = [
            f"# {rec['id']} {label}",
            "",
            f"application_key: `{key}`",
            "",
            "## application result",
            "",
            f"- before comparison/monitoring/evidence: {before.get('comparison_status')} / {before.get('monitoring_status')} / {before.get('evidence_status')}",
            f"- after comparison/monitoring/evidence: {after.get('comparison_status')} / {after.get('monitoring_status')} / {after.get('evidence_status')}",
            f"- unresolved before: `{before.get('unresolved_reason')}`",
            f"- unresolved after: `{after.get('unresolved_reason')}`",
            "",
            "## World tuple",
            "",
            "```json",
            json.dumps(rec["world_tuple"], indent=2, default=str),
            "```",
            "",
            "## holes mentioning this measurement",
            "",
            "```json",
            json.dumps(rec["holes"], indent=2, default=str),
            "```",
            "",
            "## construction origin / grounding pointer",
            "",
            f"proposals on State C: {origins.get('proposals')}",
            "",
            "Source locations live in sealed obligation-resolution packets; this World copy carries relation-level grounding in world.sqlite.origins.json.",
            "",
        ]
        (traces_dir / f"{rec['id']}_{label}.md").write_text("\n".join(md), encoding="utf-8")
    (traces_dir / "index.json").write_text(json.dumps(records, indent=2, default=str) + "\n", encoding="utf-8")
    return records


def run_deterministic() -> dict:
    RUNS.mkdir(parents=True, exist_ok=True)
    freeze = freeze_inputs()
    worlds = materialize_all()
    for state_id in STATES_USED:
        write_header(STATES / state_id)
    sql_hash = sha256_file(CONSUMERS / "sql" / "monitoring_analysis.sql")
    py_hash = sha256_file(CONSUMERS / "python" / "monitoring_analysis.py")
    consumer_hashes = {
        "sql": sql_hash,
        "python": py_hash,
        "frozen_before_state_b": True,
    }
    (ROOT / "frozen" / "consumer_hashes.json").write_text(json.dumps(consumer_hashes, indent=2) + "\n", encoding="utf-8")

    summaries = {}
    for state_id in STATES_USED:
        summaries[state_id] = _run_consumer_isolated(state_id, OUTPUTS / state_id)

    after_sql = sha256_file(CONSUMERS / "sql" / "monitoring_analysis.sql")
    after_py = sha256_file(CONSUMERS / "python" / "monitoring_analysis.py")
    rewrite_count = int(after_sql != sql_hash) + int(after_py != py_hash)

    DIFFS.mkdir(parents=True, exist_ok=True)
    ab = diff_states(
        OUTPUTS / "state_a" / "monitoring_analysis.csv",
        OUTPUTS / "state_b" / "monitoring_analysis.csv",
        "state_a",
        "state_b",
    )
    bc = diff_states(
        OUTPUTS / "state_b" / "monitoring_analysis.csv",
        OUTPUTS / "state_c" / "monitoring_analysis.csv",
        "state_b",
        "state_c",
    )
    write_diff(ab, DIFFS / "a_to_b_rows.csv", DIFFS / "a_to_b_summary.md")
    write_diff(bc, DIFFS / "b_to_c_rows.csv", DIFFS / "b_to_c_summary.md")
    leakage = audit_consumers()
    failed = _failed_candidate(STATES / "state_c" / "accepted" / "world.sqlite", OUTPUTS / "state_c")
    reopen = {state_id: _reopen(state_id, OUTPUTS / state_id / "monitoring_analysis.csv") for state_id in STATES_USED}
    traces = _write_traces()
    payload = {
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "freeze": freeze,
        "worlds": worlds,
        "consumer_hashes": consumer_hashes,
        "consumer_rewrite_count": rewrite_count,
        "summaries": summaries,
        "diffs": {"a_to_b": ab["summary"], "b_to_c": bc["summary"]},
        "leakage": leakage,
        "failure_path": failed,
        "reopen": reopen,
        "n_traces": len(traces),
        "state_d": "skipped",
    }
    (RUNS / "deterministic.json").write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")
    return payload


if __name__ == "__main__":
    run_deterministic()
