"""Structural admission only. No cue-list verifier. UNRESOLVED is a successful result."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    load_dispositions,
)

IDENTITY_DISPS = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
VALID_IDENTITY = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
VALID_OTHER = {"ACCEPT", "REJECT", "UNRESOLVED", "PRESENT", "ABSENT"}
CLOSURE = {"SAME_ENTITY", "DISTINCT"}


def _packet_for(workspace: Path, obligation_id: str) -> dict[str, Any]:
    packets = workspace / "04_packets"
    path = packets / f"{obligation_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    matches = list(packets.glob(f"*{obligation_id}*.json")) if packets.is_dir() else []
    if matches:
        return json.loads(matches[0].read_text())
    return {}


def _packet_blob(packet: dict[str, Any]) -> str:
    return json.dumps(packet).lower()


def structural_admit(proposed: str, *, is_identity: bool, evidence: list, packet: dict[str, Any]) -> tuple[str, str]:
    disp = proposed.upper()
    if is_identity and disp not in VALID_IDENTITY:
        return "UNRESOLVED", "invalid_disposition"
    if not is_identity and disp not in VALID_OTHER | VALID_IDENTITY:
        return "UNRESOLVED", "invalid_disposition"
    if disp in CLOSURE:
        if not evidence:
            return "UNRESOLVED", "missing_required_grounding"
        blob = _packet_blob(packet)
        cited = []
        for item in evidence:
            if isinstance(item, dict):
                cited.append(str(item.get("source_path") or item.get("location") or ""))
            else:
                cited.append(str(item))
        if packet and cited and not any(token.lower() in blob for token in cited if token):
            return "UNRESOLVED", "grounding_not_in_packet"
    return disp, "admitted"


def admit_workspace(workspace: Path) -> list[dict[str, Any]]:
    path = workspace / "05_dispositions.json"
    rows = load_dispositions(path)
    audit: list[dict[str, Any]] = []
    admitted: list[dict[str, Any]] = []
    for row in rows:
        proposed = str(row.get("disposition") or "UNRESOLVED").upper()
        values = row.get("values") if isinstance(row.get("values"), dict) else {}
        left = str(values.get("left") or row.get("left") or "")
        right = str(values.get("right") or row.get("right") or "")
        oid = str(row.get("obligation_id") or "")
        is_identity = proposed in IDENTITY_DISPS or "identity" in str(row.get("relation") or "").lower()
        evidence = row.get("supporting_evidence") or row.get("grounding") or []
        if not isinstance(evidence, list):
            evidence = [evidence]
        packet = _packet_for(workspace, oid) if is_identity else {}
        final, reason = structural_admit(proposed, is_identity=is_identity, evidence=evidence, packet=packet)
        updated = dict(row)
        updated["original_disposition"] = proposed
        updated["final_admitted_disposition"] = final
        updated["disposition"] = final
        updated["admission_reason"] = reason
        if is_identity:
            audit.append(
                {
                    "candidate": {"left": left, "right": right},
                    "packet": oid,
                    "initial_disposition": proposed,
                    "support_evidence": evidence,
                    "support_claim": row.get("support_claim") or row.get("rationale"),
                    "structural_reason": reason,
                    "final_disposition": final,
                    "verifier_result": None,
                }
            )
        admitted.append(updated)
    path.write_text(json.dumps(admitted, indent=2) + "\n")
    (workspace / "05_adjudication_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit
