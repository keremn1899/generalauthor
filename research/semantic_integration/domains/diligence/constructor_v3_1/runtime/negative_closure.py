"""Narrow DISTINCT negative-closure gate. Isolated behind this interface.

Does not run on SAME or UNRESOLVED. Never upgrades UNRESOLVED. Never searches sources.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

GATE_TIMEOUT = 180

GATE_PROMPT = """You are a negative-closure gate for one identity proposition.

You receive:
- candidate.json (two referents)
- relation_contract.json (identity relation contract)
- packet.json (bounded evidence only)
- proposal.json (proposed DISTINCT, support_claim, grounding)

Your only job: decide whether the cited evidence ESTABLISHES that the two referents cannot denote the same entity under the relation contract.

Evidence of difference is not automatically evidence of distinct identity.

DISTINCT requires evidence that the two referents cannot denote the same entity. Examples of potentially establishing evidence: an explicit source statement that the entities are distinct; mutually incompatible authoritative identifiers; simultaneously active incompatible legal identities; authoritative registry facts that exclude identity.

Do NOT treat as automatically establishing DISTINCT: name variation; legal-form suffix difference alone; jurisdiction mismatch alone; address variation alone; missing identifiers; partial contradictory metadata; weak similarity mismatch; absence of corroboration.

Do not invent candidates. Do not search any file except candidate.json, relation_contract.json, packet.json, and proposal.json. Do not change grounding. Do not output SAME_ENTITY.

Write gate_result.json as:
{"result": "SUPPORTED_DISTINCT" | "NOT_ESTABLISHED", "reason": "one sentence"}
"""


def parse_gate_result(text: str) -> dict[str, str]:
    if not text:
        return {"result": "NOT_ESTABLISHED", "reason": "empty_gate_output"}
    matches = re.findall(r"\{[^{}]*\"result\"[^{}]*\}", text, flags=re.DOTALL)
    for blob in reversed(matches):
        try:
            payload = json.loads(blob)
        except json.JSONDecodeError:
            continue
        result = str(payload.get("result") or "").upper()
        if result in {"SUPPORTED_DISTINCT", "NOT_ESTABLISHED"}:
            return {"result": result, "reason": str(payload.get("reason") or "")}
    upper = text.upper()
    if "SUPPORTED_DISTINCT" in upper and "NOT_ESTABLISHED" not in upper:
        return {"result": "SUPPORTED_DISTINCT", "reason": "parsed_from_text"}
    return {"result": "NOT_ESTABLISHED", "reason": "unparsed_gate_output"}


def evaluate_distinct(
    *,
    candidate: dict[str, str],
    packet: dict[str, Any],
    support_claim: str,
    grounding: list,
    contract: dict[str, Any] | None = None,
    run_agent=None,
) -> dict[str, str]:
    """Return SUPPORTED_DISTINCT or NOT_ESTABLISHED. Fail closed on errors."""
    if run_agent is None:
        return _run_isolated_gate(
            candidate=candidate,
            packet=packet,
            support_claim=support_claim,
            grounding=grounding,
            contract=contract,
        )
    return run_agent(
        candidate=candidate,
        packet=packet,
        support_claim=support_claim,
        grounding=grounding,
        contract=contract,
    )


def _run_isolated_gate(
    *,
    candidate: dict[str, str],
    packet: dict[str, Any],
    support_claim: str,
    grounding: list,
    contract: dict[str, Any] | None,
) -> dict[str, str]:
    from research.semantic_integration.domains.diligence.constructor_v3_1.agent import run_v3_agent
    from research.semantic_integration.domains.diligence.constructor_v3_1.isolation import (
        new_live_workspace,
        preflight_isolation,
        remove_live_workspace,
    )
    from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.contracts import (
        IDENTITY_CONTRACT,
        contract_to_dict,
    )

    live = new_live_workspace()
    try:
        (live / "candidate.json").write_text(json.dumps(candidate, indent=2) + "\n")
        (live / "packet.json").write_text(json.dumps(packet, indent=2) + "\n")
        (live / "proposal.json").write_text(
            json.dumps(
                {
                    "proposed": "DISTINCT",
                    "support_claim": support_claim,
                    "grounding": grounding,
                },
                indent=2,
            )
            + "\n"
        )
        (live / "relation_contract.json").write_text(
            json.dumps(contract or contract_to_dict(IDENTITY_CONTRACT), indent=2) + "\n"
        )
        (live / "README.md").write_text("Negative-closure gate. Packet only.\n")
        preflight_isolation(live)
        agent = run_v3_agent(workspace=live, prompt=GATE_PROMPT, timeout_seconds=GATE_TIMEOUT)
        result = parse_gate_result((agent.get("stdout") or "") + "\n" + (agent.get("stderr") or ""))
        path = live / "gate_result.json"
        if path.exists():
            try:
                payload = json.loads(path.read_text())
                got = str(payload.get("result") or "").upper()
                if got in {"SUPPORTED_DISTINCT", "NOT_ESTABLISHED"}:
                    result = {"result": got, "reason": str(payload.get("reason") or "")}
            except json.JSONDecodeError:
                pass
        result["model"] = agent.get("reported_model") or agent.get("model")
        result["timed_out"] = bool(agent.get("timed_out"))
        if result.get("timed_out"):
            result = {"result": "NOT_ESTABLISHED", "reason": "gate_timeout"}
        return result
    except Exception as exc:
        return {"result": "NOT_ESTABLISHED", "reason": f"gate_error:{exc}"}
    finally:
        remove_live_workspace(live)
