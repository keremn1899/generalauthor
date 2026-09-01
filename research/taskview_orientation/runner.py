"""A real five-turn episode runner with injectable stateful participant sessions."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Protocol

from research.taskview_orientation.fixture import (
    FROZEN_ROOT,
    SOURCE_ROOT,
    copy_frozen_task_view,
)
from research.taskview_orientation.oracle import (
    load_prompts,
    score_answer,
    validate_answer,
)
from research.taskview_orientation.surface import ExperimentTaskViewSurface
from research.taskview_orientation.telemetry import (
    FrozenSpanClassifier,
    TelemetryRecorder,
    visible_bytes,
)
from research.taskview_orientation.tools import EpisodeTools


PHASE4_REPLACEMENT = FROZEN_ROOT / "phase4" / "tests" / "checkout_contract.py"
CLASSIFICATION_PATH = FROZEN_ROOT / "span_classification.json"
TOOL_SCHEMAS_PATH = FROZEN_ROOT / "tool_schemas.json"


@dataclass(frozen=True)
class ParticipantTurn:
    answer: dict[str, Any]
    session_id: str
    provider_input_tokens: int | None = None
    provider_output_tokens: int | None = None


class StatefulParticipantSession(Protocol):
    """One provider session object must service all five sequential turns."""

    session_id: str

    def turn(
        self,
        *,
        phase: int,
        prompt: str,
        answer_fields: list[str],
        tools: EpisodeTools,
    ) -> ParticipantTurn: ...


SessionFactory = Callable[[str, list[dict[str, Any]], str], StatefulParticipantSession]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class EpisodeRunner:
    def __init__(self, *, session_factory: SessionFactory) -> None:
        self.session_factory = session_factory

    def run(
        self,
        *,
        arm: str,
        replicate: int,
        output_root: Path | str,
        condition: str | None = None,
        system_prompt_suffix: str = "",
    ) -> dict[str, Any]:
        if arm not in {"RAW", "TASKVIEW"}:
            raise ValueError("arm must be RAW or TASKVIEW")
        run_root = Path(output_root)
        if run_root.exists():
            raise FileExistsError(f"refusing to replace episode directory: {run_root}")
        source_root = run_root / "source"
        scratch_root = run_root / "scratch"
        shutil.copytree(SOURCE_ROOT, source_root)
        scratch_root.mkdir(parents=True)

        episode_id = f"{arm.lower()}-r{replicate}-{uuid.uuid4().hex[:8]}"
        telemetry = TelemetryRecorder(
            episode_id=episode_id, arm=arm, replicate=replicate
        )
        view = None
        treatment_surface = None
        if arm == "TASKVIEW":
            view = copy_frozen_task_view(run_root / "taskview.sqlite")
            treatment_surface = ExperimentTaskViewSurface(view)
            if condition in {"T00", "T10", "T01", "T11"}:
                from research.taskview_orientation.bounded_reliance.surface import (
                    wrap_surface,
                )

                treatment_surface = wrap_surface(
                    treatment_surface,
                    condition=condition,
                    source_root=source_root,
                )
            elif condition in {"ATOMIC", "COMPILED"}:
                from research.taskview_orientation.compiled_projection.surface import (
                    wrap_surface as wrap_compiled_surface,
                )

                treatment_surface = wrap_compiled_surface(
                    treatment_surface,
                    condition=condition,
                )
        tools = EpisodeTools(
            source_root=source_root,
            scratch_root=scratch_root,
            telemetry=telemetry,
            taskview=treatment_surface,
        )

        prompts = load_prompts()
        tool_schemas = json.loads(TOOL_SCHEMAS_PATH.read_text(encoding="utf-8"))
        visible_schemas = list(tool_schemas["native"])
        if arm == "TASKVIEW":
            visible_schemas.extend(tool_schemas["taskview"])
        system_prompt = prompts["common_system"] + "\n\n" + prompts["arms"][arm]
        if system_prompt_suffix:
            system_prompt = system_prompt + "\n\n" + system_prompt_suffix
        session = self.session_factory(system_prompt, visible_schemas, arm)
        original_session_id = session.session_id
        telemetry.record(
            "SESSION_START",
            phase=0,
            session_id=original_session_id,
            system_prompt_sha256=hashlib.sha256(system_prompt.encode()).hexdigest(),
            tool_schema_sha256=hashlib.sha256(
                json.dumps(visible_schemas, sort_keys=True).encode()
            ).hexdigest(),
            model_visible_input_bytes=(
                len(system_prompt.encode("utf-8")) + visible_bytes(visible_schemas)
            ),
        )

        answers = []
        phase_scores = []
        for phase_record in prompts["phases"]:
            phase = phase_record["phase"]
            if phase == 4:
                target = source_root / "tests" / "checkout_contract.py"
                before_hash = _sha256(target)
                replacement = PHASE4_REPLACEMENT.read_bytes()
                target.write_bytes(replacement)
                tools.mark_phase4_source()
                telemetry.record(
                    "HARNESS_MUTATION",
                    phase=phase,
                    boundary="after_phase_3_commit_before_phase_4_prompt",
                    source_path="tests/checkout_contract.py",
                    before_sha256=before_hash,
                    after_sha256=_sha256(target),
                    changed_bytes=len(replacement),
                    taskview_silently_repaired=False,
                )
            tools.set_phase(phase)
            prompt = phase_record["prompt"]
            telemetry.record(
                "TURN_INPUT",
                phase=phase,
                session_id=original_session_id,
                prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),
                model_visible_input_bytes=len(prompt.encode("utf-8")),
            )
            turn_started_ns = time.perf_counter_ns()
            turn = session.turn(
                phase=phase,
                prompt=prompt,
                answer_fields=phase_record["answer_fields"],
                tools=tools,
            )
            if session.session_id != original_session_id or turn.session_id != original_session_id:
                raise RuntimeError("participant session/context changed within the episode")
            validate_answer(phase=phase, answer=turn.answer, source_root=source_root)
            answer_copy = {"phase": phase, "answer": turn.answer}
            answers.append(answer_copy)
            score = score_answer(phase, turn.answer)
            phase_scores.append(score)
            telemetry.record(
                "TURN_OUTPUT",
                phase=phase,
                session_id=original_session_id,
                final_structured_answer=turn.answer,
                source_citations=turn.answer["citations"],
                model_visible_output_bytes=visible_bytes(turn.answer),
                provider_input_tokens=turn.provider_input_tokens,
                provider_output_tokens=turn.provider_output_tokens,
                wall_time_ms=(time.perf_counter_ns() - turn_started_ns) / 1_000_000,
            )
            (run_root / "answers.partial.json").write_text(
                json.dumps(answers, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        telemetry.record(
            "SESSION_END",
            phase=5,
            session_id=original_session_id,
            turns_committed=5,
        )
        classifier = FrozenSpanClassifier.load(CLASSIFICATION_PATH)
        metrics = classifier.aggregate(telemetry.events)
        telemetry.write_jsonl(run_root / "telemetry.jsonl")
        record = {
            "episode_id": episode_id,
            "arm": arm,
            "condition": condition,
            "replicate": replicate,
            "session_id": original_session_id,
            "turns": 5,
            "phase4_replacement_sha256": _sha256(
                source_root / "tests" / "checkout_contract.py"
            ),
            "answers": answers,
            "oracle_scores": phase_scores,
            "metrics": metrics,
            "apparatus_only": True,
            "participant_model_invoked": False,
        }
        (run_root / "record.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        if view is not None:
            view.close()
        return record


class ScriptedApparatusParticipant:
    """Deterministic source-derived lifecycle probe; never an experimental participant."""

    def __init__(self, _system: str, _schemas: list[dict[str, Any]], arm: str) -> None:
        self.arm = arm
        self.session_id = f"scripted-{arm.lower()}-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def _cite(path: str, start: int, end: int) -> dict[str, Any]:
        return {"path": path, "start_line": start, "end_line": end}

    def _raw_orientation(self, phase: int, tools: EpisodeTools) -> None:
        if phase == 1:
            tools.search_source("jsonlib|migration|production", ".")
            tools.read_source("tasks/migrate-jsonlib-v3.md", 1, 19)
            tools.read_source("deploy/production-services.yaml", 1, 8)
            tools.read_source("deploy/service-components.yaml", 1, 12)
        elif phase == 2:
            tools.search_source("adapter|canonical|Decimal", ".")
            tools.read_source("tasks/migrate-jsonlib-v3.md", 3, 10)
        elif phase == 3:
            tools.search_source("boundary|unresolved|wildcard", ".")
            tools.read_source("architecture/partner-gateway.md", 3, 10)
            tools.read_source("runtime/dynamic-consumers.md", 3, 10)
        elif phase == 5:
            tools.search_source("verified|contract|unresolved", ".")
            tools.read_source("tasks/migrate-jsonlib-v3.md", 15, 19)

    def turn(
        self,
        *,
        phase: int,
        prompt: str,
        answer_fields: list[str],
        tools: EpisodeTools,
    ) -> ParticipantTurn:
        del prompt, answer_fields
        if self.arm == "RAW":
            self._raw_orientation(phase, tools)
        elif phase == 1:
            tools.describe()
            tools.query_sql("SELECT service_id FROM requires_change ORDER BY service_id")
        elif phase == 2:
            tools.query_sql(
                "SELECT a.service_id, p.adapter_id FROM affected_service a "
                "JOIN protected_by p ON p.service_id = a.service_id"
            )
        elif phase == 3:
            tools.query_sql("SELECT subject_id, basis FROM excluded")
            tools.query_sql("SELECT subject_id FROM unresolved_scope")
        elif phase == 4:
            tools.assertion(
                action="RETRACT",
                relation="verified_by",
                values={
                    "service": "service:checkout",
                    "test": "test:checkout-contract",
                },
            )
        elif phase == 5:
            tools.rerun("verification_gap")
            tools.query_sql("SELECT service_id FROM verification_gap ORDER BY service_id")

        if phase == 1:
            tools.read_source("services/checkout/json_codec.py", 6, 12)
            tools.read_source("vendor/jsonlib_v3_migration.md", 3, 10)
            answer = {
                "direct_change_services": ["service:checkout"],
                "decoding_invariants": ["comments accepted", "numbers remain Decimal"],
                "v3_call_shape": 'Decoder(allow_comments=True, number_mode="decimal").decode(payload)',
                "citations": [
                    self._cite("services/checkout/json_codec.py", 6, 12),
                    self._cite("vendor/jsonlib_v3_migration.md", 3, 10),
                ],
            }
        elif phase == 2:
            tools.read_source("services/reporting/json_adapter.py", 4, 13)
            tools.read_source("services/reporting/report_builder.py", 6, 12)
            tools.read_source("tests/reporting_contract.py", 4, 5)
            answer = {
                "protected_service": "service:reporting",
                "direct_edit_required": False,
                "adapter": "adapter:reporting-json-v3",
                "canonical_key_behavior": "sort_keys=True is translated to canonical_keys=True",
                "decimal_serialization_behavior": "decimal_mode=string is translated to decimal-string and preserves Decimal as a quoted string with scale",
                "verification_assertion": "build_report() == '{\"amount\":\"10.50\",\"id\":\"r-7\"}'",
                "citations": [
                    self._cite("services/reporting/json_adapter.py", 4, 13),
                    self._cite("services/reporting/report_builder.py", 6, 12),
                    self._cite("tests/reporting_contract.py", 4, 5),
                ],
            }
        elif phase == 3:
            tools.read_source("services/partner_gateway/protocol.py", 4, 9)
            tools.read_source("runtime/consumer_registry.py", 1, 10)
            answer = {
                "boundary_subject": "service:partner-gateway",
                "boundary_status": "EXCLUDED",
                "byte_stable_wire_field": "signed_body",
                "unresolved_subject": "service:external-worker",
                "unresolved_status": "UNRESOLVED",
                "dynamic_lookup_mechanism": "resolve_consumer uses REGISTRY wildcard plugins.{tenant_alias}.JsonConsumer",
                "whole_world_complete": False,
                "citations": [
                    self._cite("architecture/partner-gateway.md", 3, 10),
                    self._cite("services/partner_gateway/protocol.py", 4, 9),
                    self._cite("runtime/dynamic-consumers.md", 3, 10),
                    self._cite("runtime/consumer_registry.py", 1, 10),
                ],
            }
        elif phase == 4:
            tools.read_source("tests/checkout_contract.py", 1, 6)
            answer = {
                "invalidated_verification": ["service:checkout", "test:checkout-contract"],
                "missing_behaviors": ["comment acceptance", "Decimal preservation"],
                "downstream_result_state": "verification_gap must be treated as stale until rerun",
                "retained_state_update": "retract verified_by(service:checkout, test:checkout-contract)",
                "citations": [self._cite("tests/checkout_contract.py", 4, 6)],
            }
        else:
            tools.read_source("services/checkout/json_codec.py", 6, 12)
            tools.read_source("tests/checkout_contract.py", 1, 6)
            tools.read_source("runtime/dynamic-consumers.md", 6, 8)
            tools.read_source("architecture/partner-gateway.md", 9, 10)
            answer = {
                "current_verification_gap": ["service:checkout"],
                "proposed_replacement_verification": [
                    "decode a payload containing a comment",
                    'assert total equals Decimal("10.50") and remains a Decimal',
                ],
                "other_gaps_in_affected_service": [],
                "completeness_universe": "affected_service",
                "whole_world_complete": False,
                "whole_world_blockers": [
                    "service:external-worker unresolved",
                    "partner boundary internals opaque",
                ],
                "citations": [
                    self._cite("services/checkout/json_codec.py", 6, 12),
                    self._cite("tests/checkout_contract.py", 4, 6),
                    self._cite("runtime/dynamic-consumers.md", 6, 8),
                    self._cite("architecture/partner-gateway.md", 9, 10),
                ],
            }
        return ParticipantTurn(answer=answer, session_id=self.session_id)


def scripted_session_factory(
    system: str, schemas: list[dict[str, Any]], arm: str
) -> StatefulParticipantSession:
    return ScriptedApparatusParticipant(system, schemas, arm)
