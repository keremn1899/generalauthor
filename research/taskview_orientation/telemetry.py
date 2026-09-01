"""Raw telemetry, frozen span classification, and deterministic aggregation."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


LABELS = ("LOCAL_ORACLE", "ORIENTATION_SUPPORT", "IRRELEVANT")


def taskview_variant(event: dict[str, Any]) -> str:
    """Classify the v0.1 describe surface without changing operation totals."""

    operation = event.get("taskview_operation")
    if operation != "describe":
        return str(operation)
    arguments = event.get("tool_arguments") or {}
    if arguments.get("why") is not None:
        return "describe_why"
    if arguments.get("relation") is not None:
        return "describe_relation"
    return "describe_catalog"


def visible_bytes(value: Any) -> int:
    return len(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


class TelemetryRecorder:
    """Append-only in-memory events that can be preserved as JSONL."""

    def __init__(self, *, episode_id: str, arm: str, replicate: int) -> None:
        self.episode_id = episode_id
        self.arm = arm
        self.replicate = replicate
        self.events: list[dict[str, Any]] = []
        self._sequence = 0

    def record(self, event_type: str, *, phase: int, **payload: Any) -> dict[str, Any]:
        self._sequence += 1
        event = {
            "sequence": self._sequence,
            "timestamp_ns": time.time_ns(),
            "episode_id": self.episode_id,
            "arm": self.arm,
            "replicate": self.replicate,
            "phase": phase,
            "turn_index": phase,
            "event_type": event_type,
            **payload,
        }
        self.events.append(event)
        return event

    def write_jsonl(self, path: Path | str) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            "".join(json.dumps(event, sort_keys=True) + "\n" for event in self.events),
            encoding="utf-8",
        )


class FrozenSpanClassifier:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    @classmethod
    def load(cls, path: Path | str) -> "FrozenSpanClassifier":
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def classify_line(
        self,
        *,
        phase: int,
        path: str,
        line: int,
        source_version: str = "initial",
    ) -> str:
        phase_config = self.config["phases"][str(phase)]
        matches = []
        for span in phase_config["spans"]:
            required_version = span.get("source_version")
            if required_version and required_version != source_version:
                continue
            if (
                span["path"] == path
                and span["start_line"] <= line <= span["end_line"]
            ):
                matches.append(span["label"])
        if len(set(matches)) > 1:
            raise ValueError(f"overlapping frozen labels for phase {phase}, {path}:{line}")
        return matches[0] if matches else self.config["default_label"]

    def is_broad_search(self, *, phase: int, scope: str) -> bool:
        normalized = PurePosixPath(scope or ".").as_posix().rstrip("/") or "."
        rules = self.config["broad_search_rules"]
        if normalized in rules["repository_root_scopes"]:
            return True
        local = self.config["phases"][str(phase)]["local_directories"]
        if rules["outside_phase_local_directories"]:
            inside_local = any(
                normalized == directory or normalized.startswith(directory + "/")
                for directory in local
            )
            if not inside_local:
                return True
        if rules["cross_service_scope_after_target_known"] and normalized == "services":
            return True
        return False

    def _event_label_bytes(self, event: dict[str, Any]) -> dict[str, int]:
        raw = dict.fromkeys(LABELS, 0)
        for segment in event.get("segments", []):
            label = self.classify_line(
                phase=event["phase"],
                path=segment["path"],
                line=segment["line"],
                source_version=segment.get("source_version", "initial"),
            )
            raw[label] += int(segment["bytes"])
        source_total = sum(raw.values())
        visible_total = int(event.get("model_visible_output_bytes", source_total))
        if source_total == 0:
            raw["IRRELEVANT"] = visible_total
            return raw
        allocated: dict[str, int] = {}
        remaining = visible_total
        nonzero = [label for label in LABELS if raw[label]]
        for label in nonzero[:-1]:
            amount = visible_total * raw[label] // source_total
            allocated[label] = amount
            remaining -= amount
        allocated[nonzero[-1]] = remaining
        return {label: allocated.get(label, 0) for label in LABELS}

    @staticmethod
    def _overlaps(segment: dict[str, Any], support: list[Any]) -> bool:
        path, start, end = support
        return (
            segment["path"] == path
            and start <= segment["line"] <= end
        )

    def aggregate(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        source_events = [
            event
            for event in events
            if event["event_type"] in {"SOURCE_READ", "SOURCE_SEARCH"}
            or (
                event["event_type"] == "TOOL_ERROR"
                and event.get("tool_name") in {"read_source", "search_source"}
            )
        ]
        label_bytes = dict.fromkeys(LABELS, 0)
        post_label_bytes = dict.fromkeys(LABELS, 0)
        event_labels: dict[int, dict[str, int]] = {}
        irrelevant_files: set[str] = set()
        for event in source_events:
            counts = self._event_label_bytes(event)
            event_labels[event["sequence"]] = counts
            for label, count in counts.items():
                label_bytes[label] += count
                if event["phase"] >= 2:
                    post_label_bytes[label] += count
            for segment in event.get("segments", []):
                if self.classify_line(
                    phase=event["phase"],
                    path=segment["path"],
                    line=segment["line"],
                    source_version=segment.get("source_version", "initial"),
                ) == "IRRELEVANT":
                    irrelevant_files.add(segment["path"])

        taskview_result_events = [
            event
            for event in events
            if event["event_type"] == "TASKVIEW_TOOL"
            or (
                event["event_type"] == "TOOL_ERROR"
                and event.get("tool_name") in {"describe", "query_sql", "assertion", "rerun"}
            )
        ]
        taskview_post = sum(
            int(event.get("model_visible_output_bytes", 0))
            for event in taskview_result_events
            if event["phase"] >= 2
        )
        o_post = (
            post_label_bytes["ORIENTATION_SUPPORT"]
            + post_label_bytes["IRRELEVANT"]
        )
        all_source = sum(label_bytes.values())

        broad_searches = [
            event
            for event in source_events
            if event["event_type"] == "SOURCE_SEARCH"
            and self.is_broad_search(phase=event["phase"], scope=event["search_scope"])
        ]
        seen_searches: set[tuple[str, str]] = set()
        repeated_broad = 0
        for event in broad_searches:
            signature = (event["search_query"], event["search_scope"])
            if signature in seen_searches:
                repeated_broad += 1
            seen_searches.add(signature)

        seen_orientation_lines: set[tuple[str, int]] = set()
        repeated_orientation_reads = 0
        for event in source_events:
            repeated_in_event = False
            for segment in event.get("segments", []):
                label = self.classify_line(
                    phase=event["phase"],
                    path=segment["path"],
                    line=segment["line"],
                    source_version=segment.get("source_version", "initial"),
                )
                key = (segment["path"], segment["line"])
                if label == "ORIENTATION_SUPPORT" and key in seen_orientation_lines:
                    repeated_in_event = True
                if label == "ORIENTATION_SUPPORT":
                    seen_orientation_lines.add(key)
            repeated_orientation_reads += int(repeated_in_event)

        phase_focus: dict[str, Any] = {}
        phase_starts = {
            event["phase"]: event
            for event in events
            if event["event_type"] == "TURN_INPUT"
        }
        for phase in range(1, 6):
            phase_sources = [event for event in source_events if event["phase"] == phase]
            first_local = next(
                (
                    event
                    for event in phase_sources
                    if event["event_type"] == "SOURCE_READ"
                    if event_labels[event["sequence"]]["LOCAL_ORACLE"] > 0
                ),
                None,
            )
            before = [
                event
                for event in phase_sources
                if first_local is None or event["sequence"] < first_local["sequence"]
            ]
            phase_focus[str(phase)] = {
                "first_local_sequence": first_local["sequence"] if first_local else None,
                "bytes_before_first_local": sum(
                    int(event.get("model_visible_output_bytes", 0)) for event in before
                ),
                "time_ms_before_first_local": (
                    (first_local["timestamp_ns"] - phase_starts[phase]["timestamp_ns"])
                    / 1_000_000
                    if first_local and phase in phase_starts
                    else None
                ),
            }

        reconstructions = []
        semantic_events = self.config["semantic_reconstruction_events"]
        for event_id, definition in semantic_events.items():
            for phase in definition["reuse_phases"]:
                phase_sources = [event for event in source_events if event["phase"] == phase]
                first_local_sequence = phase_focus[str(phase)]["first_local_sequence"]
                for source_event in phase_sources:
                    if (
                        first_local_sequence is not None
                        and source_event["sequence"] >= first_local_sequence
                    ):
                        break
                    if any(
                        self._overlaps(segment, support)
                        for segment in source_event.get("segments", [])
                        for support in definition["support_spans"]
                    ):
                        reconstructions.append(
                            {
                                "event": event_id,
                                "phase": phase,
                                "observable_at_sequence": source_event["sequence"],
                            }
                        )
                        break

        logical_tool_calls = [
            event for event in events if event["event_type"] == "LOGICAL_TOOL_CALL"
        ]
        tool_calls = logical_tool_calls or [
            event for event in events if event["event_type"] == "TOOL_CALL"
        ]
        taskview_logical_calls = [
            {
                **event,
                "taskview_operation": event.get("taskview_operation") or event.get("tool_name"),
            }
            for event in tool_calls
            if event.get("tool_name") in {"describe", "query_sql", "assertion", "rerun"}
        ]
        tool_calls_by_type = dict(
            sorted(
                (name, sum(event["tool_name"] == name for event in tool_calls))
                for name in {event["tool_name"] for event in tool_calls}
            )
        )
        taskview_calls_by_operation = dict(
            sorted(
                (
                    name,
                    sum(
                        event.get("taskview_operation") == name
                        for event in taskview_logical_calls
                    ),
                )
                for name in {
                    event["taskview_operation"]
                    for event in taskview_logical_calls
                }
            )
        )
        taskview_calls_by_variant = dict(
            sorted(
                (
                    taskview_variant(event),
                    sum(
                        taskview_variant(event) == taskview_variant(candidate)
                        for candidate in taskview_logical_calls
                    ),
                )
                for event in taskview_logical_calls
            )
        )
        taskview_visible_bytes_by_variant = dict(
            sorted(
                (
                    variant,
                    sum(
                        int(event.get("model_visible_output_bytes", 0))
                        for event in taskview_result_events
                        if taskview_variant(event) == variant
                    ),
                )
                for variant in taskview_calls_by_variant
            )
        )
        read_paths = [
            event["source_path"]
            for event in source_events
            if event["event_type"] == "SOURCE_READ"
        ]
        provider_input_tokens = [
            event["provider_input_tokens"]
            for event in events
            if event.get("provider_input_tokens") is not None
        ]
        provider_output_tokens = [
            event["provider_output_tokens"]
            for event in events
            if event.get("provider_output_tokens") is not None
        ]

        return {
            "classification_version": self.config["version"],
            "label_bytes": label_bytes,
            "post_phase1_label_bytes": post_label_bytes,
            "O_post": o_post,
            "taskview_post_bytes": taskview_post,
            "net_orientation_bytes": o_post + taskview_post,
            "focus_ratio": (
                label_bytes["LOCAL_ORACLE"] / all_source if all_source else None
            ),
            "phase_focus": phase_focus,
            "irrelevant_unique_files": sorted(irrelevant_files),
            "broad_search_calls": len(broad_searches),
            "repeated_broad_searches": repeated_broad,
            "repeated_orientation_source_reads": repeated_orientation_reads,
            "reconstruction_events": reconstructions,
            "taskview_calls": sum(
                event.get("tool_name") in {"describe", "query_sql", "assertion", "rerun"}
                for event in tool_calls
            ),
            "taskview_visible_bytes": sum(
                int(event.get("model_visible_output_bytes", 0))
                for event in taskview_result_events
            ),
            "model_visible_input_bytes": sum(
                int(event.get("model_visible_input_bytes", 0)) for event in events
            ),
            "model_visible_output_bytes": sum(
                int(event.get("model_visible_output_bytes", 0)) for event in events
            ),
            "total_model_visible_bytes": sum(
                int(event.get("model_visible_input_bytes", 0))
                + int(event.get("model_visible_output_bytes", 0))
                for event in events
            ),
            "provider_input_tokens": sum(provider_input_tokens) if provider_input_tokens else None,
            "provider_output_tokens": sum(provider_output_tokens) if provider_output_tokens else None,
            "tool_calls_by_type": tool_calls_by_type,
            "repository_search_calls": sum(
                event["event_type"] == "SOURCE_SEARCH" for event in events
            ),
            "source_read_calls": len(read_paths),
            "unique_files_read": sorted(set(read_paths)),
            "repeated_file_reads": len(read_paths) - len(set(read_paths)),
            "taskview_calls_by_operation": taskview_calls_by_operation,
            "taskview_calls_by_variant": taskview_calls_by_variant,
            "taskview_visible_bytes_by_variant": taskview_visible_bytes_by_variant,
            "tool_response_bytes_by_operation": dict(
                sorted(
                    (
                        name,
                        sum(
                            int(event.get("delivered_payload_bytes", 0))
                            for event in events
                            if event["event_type"] == "TOOL_RESULT_DELIVERED_TO_MODEL"
                            and event.get("tool_name") == name
                        ),
                    )
                    for name in {
                        event.get("tool_name")
                        for event in events
                        if event["event_type"] == "TOOL_RESULT_DELIVERED_TO_MODEL"
                    }
                )
            ),
            "tool_wall_time_ms": sum(
                float(event.get("wall_time_ms", 0))
                for event in events
                if event["event_type"]
                in {"SOURCE_READ", "SOURCE_SEARCH", "TASKVIEW_TOOL", "SCRATCH_WRITE"}
            ),
            "participant_turn_wall_time_ms": sum(
                float(event.get("wall_time_ms", 0))
                for event in events
                if event["event_type"] == "TURN_OUTPUT"
            ),
        }
