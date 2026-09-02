"""Live C2 campaign: two authorized acceptable_replacement adjudications."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.harness import coverage, established_tuples, load_oracle_document
from research.semantic_integration.harness.c2 import insert_acceptance, score_decision
from research.taskview_bom.experiment import compile_c1
from research.taskview_bom_scaling.c2.protocol import (
    participant_request,
    validate_output,
    validate_packet,
)


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
AUTHORIZED_PATH = ROOT / "authorized.json"
RESULTS = ROOT / "results"
PACKET_DIR = REPO / "research/taskview_bom_scaling/c2/packets"
ORACLE_PATH = REPO / "research/taskview_bom_scaling/c2/adjudication_oracle.json"
BOM_ORACLE = REPO / "research/taskview_bom/oracle.json"


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _strip_json_fence(text: str) -> str:
    value = text.strip()
    if value.startswith("```json") and value.endswith("```"):
        return value[7:-3].strip()
    if value.startswith("```") and value.endswith("```"):
        return value[3:-3].strip()
    return value


def extract_json_object(text: str) -> dict[str, Any]:
    raw = _strip_json_fence(text)
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and "decision" in parsed:
            return parsed
        if isinstance(parsed, dict) and isinstance(parsed.get("result"), str):
            return extract_json_object(parsed["result"])
        if isinstance(parsed, dict) and isinstance(parsed.get("result"), dict):
            return parsed["result"]
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("provider output did not contain a JSON object")
    return json.loads(raw[start : end + 1])


def load_authorized() -> dict[str, Any]:
    authorized = json.loads(AUTHORIZED_PATH.read_text(encoding="utf-8"))
    if not authorized.get("participant_execution_authorized"):
        raise RuntimeError("C2 campaign is not authorized")
    for record in authorized["frozen_packets"]:
        path = REPO / record["path"]
        if _sha256(path) != record["sha256"]:
            raise RuntimeError(f"frozen packet hash drift: {record['path']}")
    oracle = REPO / authorized["hidden_oracle"]["path"]
    if _sha256(oracle) != authorized["hidden_oracle"]["sha256"]:
        raise RuntimeError("hidden adjudication oracle hash drift")
    return authorized


def cursor_agent_provider(request: dict[str, Any], *, model: str) -> dict[str, Any]:
    prompt = (
        "You are a bounded semantic adjudicator. Do not use tools. Do not search "
        "files, the web, or any workspace. All evidence is inlined below.\n\n"
        "Return only one JSON object matching output_schema. No Markdown fences.\n\n"
        "Each grounds.record_or_span value MUST be copied verbatim from one "
        "packet.evidence[].native_location string. Do not combine, rewrite, "
        "or abbreviate locations.\n\n"
        + json.dumps(request, indent=2, sort_keys=True, ensure_ascii=False)
    )
    with tempfile.TemporaryDirectory(prefix="c2-adjudication-") as directory:
        workspace = Path(directory)
        (workspace / "README.txt").write_text(
            "Empty adjudication workspace. Do not search outside this prompt.\n",
            encoding="utf-8",
        )
        completed = subprocess.run(
            [
                "cursor-agent",
                "--print",
                "--output-format",
                "text",
                "--mode",
                "ask",
                "--trust",
                "--sandbox",
                "enabled",
                "--workspace",
                str(workspace),
                "--model",
                model,
                prompt,
            ],
            cwd=workspace,
            text=True,
            capture_output=True,
            check=False,
            timeout=300,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "cursor-agent failed: "
                + (completed.stderr or completed.stdout)[:2000]
            )
        parsed = extract_json_object(completed.stdout)
        parsed["_provider_raw"] = {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "returncode": completed.returncode,
        }
        return parsed


def _oracle_decision(oracle: dict[str, Any], packet: dict[str, Any]) -> str:
    key = packet["candidate_assertion"]["tuple"]
    for cell in oracle["cells"]:
        if cell["candidate_assertion"]["tuple"] == key:
            return str(cell["decision"])
    raise KeyError("packet is not in the hidden adjudication oracle")


def _snapshot(world: SemanticWorld) -> dict[str, list[list[Any]]]:
    return {
        name: [list(row) for row in sorted(world.relation_tuples(name))]
        for name in (
            "acceptable_replacement",
            "eligible_part",
            "voltage_compatible",
            "temperature_compatible",
            "spec_conflict",
            "candidate_replacement",
        )
    }


def run_campaign(
    *,
    live: bool = True,
    provider: Any = None,
    output_dir: Path | None = None,
    db_path: Path | None = None,
) -> dict[str, Any]:
    authorized = load_authorized()
    hidden_oracle = json.loads(ORACLE_PATH.read_text(encoding="utf-8"))
    packets = [
        json.loads((REPO / record["path"]).read_text(encoding="utf-8"))
        for record in authorized["frozen_packets"]
    ]
    out = output_dir or RESULTS
    out.mkdir(parents=True, exist_ok=True)

    work = db_path or (out / "c2-loop.sqlite")
    if work.exists():
        work.unlink()
    sidecar = Path(str(work) + ".origins.json")
    if sidecar.exists():
        sidecar.unlink()

    compilation = compile_c1(work)
    world = SemanticWorld.wrap(compilation.view, world_id="bom-c2-loop")
    for row in world.query("SELECT assertion_id, origin FROM _tv_assertions"):
        origin = (
            ConstructionOrigin.DERIVED.value
            if row["origin"] == "DERIVED"
            else ConstructionOrigin.MECHANICAL.value
        )
        world._origins[row["assertion_id"]] = origin
    world._persist_origins()

    before = _snapshot(world)
    c0 = load_oracle_document(json.loads(BOM_ORACLE.read_text(encoding="utf-8")))
    before_coverage = coverage(c0, established_tuples(world, c0))
    if before["acceptable_replacement"]:
        raise RuntimeError("C1 must not already contain acceptable_replacement")

    records: list[dict[str, Any]] = []
    provider_calls = 0
    for packet in packets:
        validate_packet(packet)
        assertion = packet["candidate_assertion"]
        key = [assertion["relation"], *assertion["tuple"]]
        if key not in authorized["authorized_assertions"]:
            raise RuntimeError("packet is outside the authorized assertion set")
        raw: dict[str, Any]
        if provider is not None:
            raw = dict(provider(participant_request(packet)))
            provider_calls += 1
        elif live:
            raw = cursor_agent_provider(
                participant_request(packet),
                model=authorized["model"],
            )
            provider_calls += 1
        else:
            raise RuntimeError("C2 requires live=True or an injected provider")
        provider_raw = raw.pop("_provider_raw", {})
        attempt = len(records) + 1
        (out / f"adjudication-{attempt:03}.stdout.txt").write_text(
            str(provider_raw.get("stdout") or json.dumps(raw)),
            encoding="utf-8",
        )
        expected = _oracle_decision(hidden_oracle, packet)
        try:
            result = validate_output(raw, packet)
            scored = score_decision(result, expected=expected)
            inserted = None
            if result["decision"] == "ACCEPT":
                inserted = insert_acceptance(world, packet, result)
            records.append(
                {
                    "candidate_assertion": assertion,
                    "result": result,
                    "score": scored,
                    "inserted": bool(inserted),
                    "assertion_id": None if inserted is None else inserted.assertion_id,
                    "provider_raw": {
                        "returncode": provider_raw.get("returncode"),
                        "stderr_bytes": len(str(provider_raw.get("stderr") or "")),
                        "stdout_bytes": len(str(provider_raw.get("stdout") or "")),
                    },
                }
            )
        except ValueError as exc:
            records.append(
                {
                    "candidate_assertion": assertion,
                    "result": raw,
                    "score": {
                        "decision": raw.get("decision"),
                        "expected": expected,
                        "decision_match": raw.get("decision") == expected,
                        "grounded": False,
                        "fully_grounded_success": False,
                        "validation_error": str(exc),
                    },
                    "inserted": False,
                    "assertion_id": None,
                    "provider_raw": {
                        "returncode": provider_raw.get("returncode"),
                        "stderr_bytes": len(str(provider_raw.get("stderr") or "")),
                        "stdout_bytes": len(str(provider_raw.get("stdout") or "")),
                    },
                }
            )
        _write(out / f"adjudication-{len(records):03}.json", records[-1])

    after = _snapshot(world)
    after_coverage = coverage(c0, established_tuples(world, c0))
    derived_unchanged = {
        name: before[name] == after[name]
        for name in (
            "eligible_part",
            "voltage_compatible",
            "temperature_compatible",
            "spec_conflict",
            "candidate_replacement",
        )
    }
    report = {
        "campaign_id": authorized["campaign_id"],
        "model": authorized["model"],
        "provider_inference_calls": provider_calls,
        "authorized_assertion_count": len(authorized["authorized_assertions"]),
        "adjudications": records,
        "before_coverage": before_coverage,
        "after_coverage": after_coverage,
        "downstream": {
            "acceptable_replacement_after": after["acceptable_replacement"],
            "derived_relations_unchanged": derived_unchanged,
            "stale_relations": world.stale_relations(),
            "origin_account": world.origin_account(),
            "construction_loop_closed": (
                after["acceptable_replacement"]
                == [
                    [
                        "part:R210",
                        "part:R200",
                        "context:high_vibration_cabinet",
                    ],
                    [
                        "part:X110",
                        "part:X160",
                        "context:outdoor_enclosure",
                    ],
                ]
                and all(derived_unchanged.values())
                and world.stale_relations() == []
                and after_coverage["frontier_tuple_count"] == 0
            ),
        },
        "fully_grounded_success_count": sum(
            1 for item in records if item["score"]["fully_grounded_success"]
        ),
    }
    _write(out / "c2_campaign_report.json", report)
    world.close()
    return report


if __name__ == "__main__":
    print(json.dumps(run_campaign(live=True)["downstream"], indent=2, sort_keys=True))
