"""Export sealed provider trajectories as chronological, model-visible transcripts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from research.taskview_orientation.freeze import sha256_file
from research.taskview_orientation.oracle import load_prompts
from research.taskview_orientation.read_surface_replay import (
    AUTHORIZED_MANIFEST_PATH,
    SEALED_CAMPAIGN_ID,
    SEALED_RESULTS_ROOT,
)
from research.taskview_orientation.runtime import answer_schema
from research.taskview_orientation.runtime_accounting import (
    _content_texts,
    _logical_calls,
    _provider_tool,
    delivered_payload_bytes,
    observations_from_trajectory,
)
from research.taskview_orientation.trajectory_export import (
    EXPORT_ROOT,
    EXPORTER_ID,
    PACKAGE_ROOT,
    SDK_CONTRACT_PREFIX,
    SELECTED,
)


UNAVAILABLE = "[not present in recorded provider trajectory]"
MUTATION_MARKER = "=== FROZEN PHASE-4 MUTATION APPLIED ==="
HR = "=" * 80


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _dumps(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _exporter_hash() -> dict[str, str]:
    return {
        "exporter_id": EXPORTER_ID,
        "export_py_sha256": sha256_file(PACKAGE_ROOT / "export.py"),
        "init_py_sha256": sha256_file(PACKAGE_ROOT / "__init__.py"),
    }


def _campaign_progress() -> dict[str, Any]:
    return json.loads((SEALED_RESULTS_ROOT / "campaign_progress.json").read_text(encoding="utf-8"))


def _campaign_seal() -> dict[str, Any]:
    return json.loads((SEALED_RESULTS_ROOT / "campaign_seal.json").read_text(encoding="utf-8"))


def _selected_episodes() -> list[dict[str, Any]]:
    progress = _campaign_progress()
    if progress["campaign_id"] != SEALED_CAMPAIGN_ID:
        raise RuntimeError("campaign id drift")
    out = []
    for spec in SELECTED:
        match = [
            item
            for item in progress["episodes_completed"]
            if item["arm"] == spec["arm"] and item["replicate"] == spec["replicate"]
        ]
        if len(match) != 1:
            raise RuntimeError(f"episode identity not unique: {spec}")
        item = dict(match[0])
        item["filename"] = spec["filename"]
        out.append(item)
    return out


def _system_prompt(arm: str) -> str:
    prompts = load_prompts()
    return prompts["common_system"] + "\n\n" + prompts["arms"][arm]


def _phase_prompt(phase: int) -> str:
    return load_prompts()["phases"][phase - 1]["prompt"]


def _participant_prompt(arm: str, phase: int, *, first_turn: bool) -> str:
    contract = SDK_CONTRACT_PREFIX + json.dumps(answer_schema(phase), sort_keys=True)
    if first_turn:
        return _system_prompt(arm) + "\n\n" + contract + "\n\n" + _phase_prompt(phase)
    return contract + "\n\n" + _phase_prompt(phase)


def _assistant_chunk(message: dict[str, Any]) -> str:
    body = message.get("message") or {}
    parts: list[str] = []
    for item in body.get("content") or []:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def _thinking_chunk(message: dict[str, Any]) -> str:
    text = message.get("text")
    return text if isinstance(text, str) else ""


def _logical_tool(message: dict[str, Any]) -> tuple[str, Any]:
    name, _canonical = _provider_tool(message)
    args = message.get("args")
    return name, args


def _result_texts(message: dict[str, Any]) -> list[str]:
    result = message.get("result")
    if result is None:
        return []
    return _content_texts(result)


class _TextStream:
    def __init__(self) -> None:
        self.kind: str | None = None
        self.parts: list[str] = []

    def flush(self, lines: list[str]) -> None:
        if self.kind is None:
            return
        text = "".join(self.parts)
        label = "THINKING" if self.kind == "thinking" else "ASSISTANT"
        lines.append(f"[{label}]")
        lines.append(text if text else UNAVAILABLE)
        lines.append("")
        self.kind = None
        self.parts = []

    def add(self, kind: str, text: str, lines: list[str]) -> None:
        if self.kind not in {None, kind}:
            self.flush(lines)
        self.kind = kind
        self.parts.append(text)


def _mutation_event(telemetry: list[dict[str, Any]]) -> dict[str, Any] | None:
    found = [item for item in telemetry if item.get("event_type") == "HARNESS_MUTATION"]
    if len(found) > 1:
        raise RuntimeError("multiple HARNESS_MUTATION events")
    return found[0] if found else None


def export_episode(episode: dict[str, Any]) -> dict[str, Any]:
    root = SEALED_RESULTS_ROOT / episode["episode_id"]
    trajectory_path = root / "provider_trajectory.jsonl"
    record_path = root / "record.json"
    telemetry_path = root / "telemetry.jsonl"
    seal_path = root / "seal.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    telemetry = _jsonl(telemetry_path)
    trajectory = _jsonl(trajectory_path)
    prompts = load_prompts()

    system = _system_prompt(episode["arm"])
    session_start = next(item for item in telemetry if item.get("event_type") == "SESSION_START")
    if _sha256_text(system) != session_start["system_prompt_sha256"]:
        raise RuntimeError("system prompt sha256 mismatch against SESSION_START")
    for phase_record in prompts["phases"]:
        turn = next(
            item
            for item in telemetry
            if item.get("event_type") == "TURN_INPUT" and int(item["phase"]) == phase_record["phase"]
        )
        if _sha256_text(phase_record["prompt"]) != turn["prompt_sha256"]:
            raise RuntimeError(f"phase {phase_record['phase']} prompt sha256 mismatch")

    allowed = {
        "search_source",
        "read_source",
        "write_scratch",
        "describe",
        "query_sql",
        "assertion",
        "rerun",
    }
    logical, _replay, _raw = _logical_calls(
        observations_from_trajectory(trajectory),
        expected_session_id=record["session_id"],
        allowed_tool_names=allowed,
    )
    expected_logical = sum(
        int(item["unique_logical_calls"])
        for item in record["execution_checks"]["accounting_reconciliations"]
    )
    expected_result_bytes = sum(
        int(item["model_visible_tool_result_bytes"])
        for item in record["execution_checks"]["accounting_reconciliations"]
    )

    lines: list[str] = []
    exporter = _exporter_hash()
    lines.extend(
        [
            HR,
            f"EPISODE: {episode['arm']} R{episode['replicate']}",
            HR,
            f"campaign id: {SEALED_CAMPAIGN_ID}",
            f"episode id: {episode['episode_id']}",
            f"trajectory episode id: {episode['trajectory_episode_id']}",
            f"replicate: {episode['replicate']}",
            f"condition: {episode['arm']}",
            f"provider/model: {record['provider']}/{record['model']}",
            f"provider session id: {record['session_id']}",
            f"source trajectory path: {trajectory_path}",
            f"source trajectory SHA-256: {seal['file_hashes']['provider_trajectory.jsonl']}",
            f"exporter version/hash: {exporter['exporter_id']} {exporter['export_py_sha256']}",
            "",
        ]
    )

    stream = _TextStream()
    current_phase: int | None = None
    first_turn = True
    seen_answer_phase: set[int] = set()
    exported_answers: dict[int, str] = {}
    tool_calls = 0
    tool_result_bytes = 0
    tool_results = 0
    open_calls: set[str] = set()
    mutation = _mutation_event(telemetry)
    mutation_emitted = False

    def start_phase(phase: int) -> None:
        nonlocal first_turn, mutation_emitted
        stream.flush(lines)
        if phase == 4 and not mutation_emitted:
            lines.append(MUTATION_MARKER)
            if mutation is None:
                lines.append(UNAVAILABLE)
            else:
                lines.append(f"event_type={mutation['event_type']}")
                lines.append(f"boundary={mutation['boundary']}")
                lines.append(f"source_path={mutation['source_path']}")
            lines.append("")
            mutation_emitted = True
        lines.append(HR)
        lines.append(f"PHASE {phase}")
        lines.append(HR)
        lines.append("")
        lines.append("[USER]")
        lines.append(_participant_prompt(episode["arm"], phase, first_turn=first_turn))
        lines.append("")
        first_turn = False

    for item in trajectory:
        phase = int(item["phase"])
        if current_phase is None or phase != current_phase:
            if current_phase is not None and phase != current_phase + 1:
                raise RuntimeError(f"phase boundary skip: {current_phase} -> {phase}")
            start_phase(phase)
            current_phase = phase

        if "event" not in item:
            result = item.get("result") or {}
            text = result.get("result")
            stream.flush(lines)
            if phase not in seen_answer_phase:
                lines.append("[PARTICIPANT ANSWER]")
                lines.append(text if isinstance(text, str) else UNAVAILABLE)
                lines.append("")
                if isinstance(text, str):
                    exported_answers[phase] = text
                    seen_answer_phase.add(phase)
            continue

        event = item["event"]
        kind = event.get("kind")
        message = event.get("sdk_message")
        if kind == "done":
            continue
        if kind == "result":
            stream.flush(lines)
            payload = event.get("result") or {}
            text = payload.get("result")
            if phase not in seen_answer_phase:
                lines.append("[PARTICIPANT ANSWER]")
                lines.append(text if isinstance(text, str) else UNAVAILABLE)
                lines.append("")
                if isinstance(text, str):
                    exported_answers[phase] = text
                    seen_answer_phase.add(phase)
            continue
        if not isinstance(message, dict):
            continue

        msg_type = message.get("type")
        if msg_type == "thinking":
            stream.add("thinking", _thinking_chunk(message), lines)
            continue
        if msg_type == "assistant":
            stream.add("assistant", _assistant_chunk(message), lines)
            continue
        stream.flush(lines)
        if msg_type == "status":
            lines.append(f"[STATUS] {message.get('status')}")
            if message.get("message"):
                lines.append(str(message.get("message")))
            lines.append("")
            continue
        if msg_type == "usage":
            lines.append("[USAGE]")
            lines.append(_dumps(message.get("usage")))
            lines.append("")
            continue
        if msg_type != "tool_call":
            lines.append(f"[{str(msg_type).upper()}]")
            lines.append(UNAVAILABLE)
            lines.append("")
            continue

        status = str(message.get("status") or "")
        call_id = str(message.get("call_id") or "")
        tool_name, raw_args = _logical_tool(message)
        if status == "running":
            open_calls.add(call_id)
            tool_calls += 1
            lines.append(f"[TOOL CALL: {tool_name}]")
            lines.append(_dumps(raw_args) if raw_args is not None else UNAVAILABLE)
            lines.append("")
            continue
        if status in {"completed", "error"}:
            open_calls.discard(call_id)
            texts = _result_texts(message)
            body = "".join(texts)
            tool_results += 1
            if texts:
                tool_result_bytes += sum(len(text.encode("utf-8")) for text in texts)
            else:
                try:
                    tool_result_bytes += delivered_payload_bytes(message.get("result"))
                except Exception:
                    pass
            lines.append("[TOOL RESULT]")
            if status == "error":
                lines.append("status=error")
            is_error = False
            result = message.get("result") or {}
            value = result.get("value") if isinstance(result, dict) else None
            if isinstance(value, dict) and value.get("isError"):
                is_error = True
            if is_error:
                lines.append("isError=true")
            lines.append(body if texts else UNAVAILABLE)
            lines.append("")
            continue
        lines.append(f"[TOOL CALL: {tool_name}]")
        lines.append(f"status={status}")
        lines.append(_dumps(raw_args) if raw_args is not None else UNAVAILABLE)
        lines.append("")

    stream.flush(lines)
    if current_phase != 5:
        raise RuntimeError(f"missing phases: last phase {current_phase}")

    answers_ok = True
    answer_notes: list[str] = []
    record_answers = {int(item["phase"]): item["answer"] for item in record["answers"]}
    for phase in range(1, 6):
        exported = exported_answers.get(phase)
        expected = record_answers[phase]
        if exported is None:
            answers_ok = False
            answer_notes.append(f"phase {phase}: missing exported answer")
            continue
        try:
            parsed = json.loads(exported)
        except json.JSONDecodeError as exc:
            answers_ok = False
            answer_notes.append(f"phase {phase}: exported answer is not JSON ({exc})")
            continue
        if parsed != expected:
            answers_ok = False
            answer_notes.append(f"phase {phase}: exported answer object mismatch")

    ordering_ok = (
        tool_calls == tool_results == len(logical) == expected_logical
        and current_phase == 5
        and not open_calls
    )
    checks = {
        "event_ordering_preserved": ordering_ok,
        "logical_tool_call_count_preserved": tool_calls == expected_logical == len(logical),
        "model_visible_tool_result_bytes_preserved": tool_result_bytes == expected_result_bytes
        == sum(call.model_visible_output_bytes for call in logical),
        "phase_boundaries_preserved": current_phase == 5
        and set(exported_answers) == {1, 2, 3, 4, 5},
        "final_answers_byte_text_equivalent": answers_ok,
    }
    text = "\n".join(lines) + "\n"
    return {
        "filename": episode["filename"],
        "text": text,
        "campaign_id": SEALED_CAMPAIGN_ID,
        "episode_id": episode["episode_id"],
        "trajectory_episode_id": episode["trajectory_episode_id"],
        "replicate": episode["replicate"],
        "condition": episode["arm"],
        "provider_session_id": record["session_id"],
        "source_trajectory_path": str(trajectory_path),
        "source_trajectory_sha256": seal["file_hashes"]["provider_trajectory.jsonl"],
        "episode_seal_sha256": episode["episode_seal_sha256"],
        "logical_event_count": len(trajectory),
        "tool_call_count": tool_calls,
        "tool_result_count": tool_results,
        "model_visible_tool_result_bytes": tool_result_bytes,
        "expected_logical_calls": expected_logical,
        "expected_model_visible_tool_result_bytes": expected_result_bytes,
        "integrity": checks,
        "answer_notes": answer_notes,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "bytes": len(text.encode("utf-8")),
    }


def run() -> dict[str, Any]:
    seal = _campaign_seal()
    if seal["status"] != "SEALED" or seal["valid"] is not True:
        raise RuntimeError("campaign is not sealed")
    if sha256_file(SEALED_RESULTS_ROOT / "campaign_progress.json") != seal["campaign_progress_sha256"]:
        raise RuntimeError("campaign_progress hash drift")
    if sha256_file(AUTHORIZED_MANIFEST_PATH) != seal["manifest_sha256"]:
        raise RuntimeError("authorized manifest hash drift")

    EXPORT_ROOT.mkdir(parents=True, exist_ok=True)
    episodes = []
    for spec in _selected_episodes():
        if sha256_file(SEALED_RESULTS_ROOT / spec["episode_id"] / "seal.json") != spec["episode_seal_sha256"]:
            raise RuntimeError(f"episode seal drift: {spec['episode_id']}")
        if sha256_file(SEALED_RESULTS_ROOT / spec["episode_id"] / "seal.json") != seal["episode_seals"][spec["episode_id"]]:
            raise RuntimeError(f"campaign episode seal mismatch: {spec['episode_id']}")
        exported = export_episode(spec)
        path = EXPORT_ROOT / spec["filename"]
        path.write_text(exported["text"], encoding="utf-8")
        exported["export_path"] = str(path)
        exported["export_sha256"] = sha256_file(path)
        if exported["export_sha256"] != exported["sha256"]:
            raise RuntimeError("written export hash mismatch")
        del exported["text"]
        episodes.append(exported)

    all_ok = all(all(item["integrity"].values()) for item in episodes)
    receipt = {
        "exporter": _exporter_hash(),
        "campaign_id": SEALED_CAMPAIGN_ID,
        "campaign_seal_sha256": sha256_file(SEALED_RESULTS_ROOT / "campaign_seal.json"),
        "manifest_sha256": seal["manifest_sha256"],
        "participant_inference_calls": 0,
        "source_episode_ids": [item["episode_id"] for item in episodes],
        "source_hashes": {
            item["episode_id"]: {
                "episode_seal_sha256": item["episode_seal_sha256"],
                "provider_trajectory_sha256": item["source_trajectory_sha256"],
            }
            for item in episodes
        },
        "export_hashes": {item["filename"]: item["export_sha256"] for item in episodes},
        "logical_event_counts": {item["filename"]: item["logical_event_count"] for item in episodes},
        "tool_call_counts": {item["filename"]: item["tool_call_count"] for item in episodes},
        "model_visible_tool_result_byte_totals": {
            item["filename"]: item["model_visible_tool_result_bytes"] for item in episodes
        },
        "integrity_check_results": {
            item["filename"]: item["integrity"] for item in episodes
        },
        "integrity_all_pass": all_ok,
        "answer_notes": {
            item["filename"]: item["answer_notes"] for item in episodes if item["answer_notes"]
        },
        "episodes": episodes,
    }
    receipt_path = EXPORT_ROOT / "EXPORT_RECEIPT.json"
    receipt_path.write_text(_dumps(receipt) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    receipt["receipt_sha256"] = sha256_file(receipt_path)
    return receipt
