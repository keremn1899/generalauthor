"""Admit P5 identity dispositions after independent R3 verification."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v2.runtime.verifier import (
    admit,
    verify_identity_disposition,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    load_dispositions,
)


IDENTITY_DISPS = {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}


def _packet_for(workspace: Path, obligation_id: str) -> dict[str, Any]:
    packets = workspace / "04_packets"
    path = packets / f"{obligation_id}.json"
    if path.exists():
        return json.loads(path.read_text())
    matches = list(packets.glob(f"*{obligation_id}*.json")) if packets.is_dir() else []
    if matches:
        return json.loads(matches[0].read_text())
    return {}


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
        is_identity = proposed in IDENTITY_DISPS or str(row.get("relation") or "").lower().find("identity") >= 0
        updated = dict(row)
        if is_identity and proposed in IDENTITY_DISPS:
            packet = _packet_for(workspace, oid)
            claim = str(row.get("support_claim") or row.get("rationale") or "")
            verification = verify_identity_disposition(
                left=left, right=right, proposed=proposed, packet=packet, support_claim=claim
            )
            final = admit(proposed, verification)
            updated["original_disposition"] = proposed
            updated["verification_result"] = verification.get("result")
            updated["final_admitted_disposition"] = final
            updated["disposition"] = final
            audit.append(
                {
                    "candidate": {"left": left, "right": right},
                    "packet": oid,
                    "initial_disposition": proposed,
                    "support_evidence": row.get("supporting_evidence") or row.get("grounding"),
                    "support_claim": claim,
                    "verifier_result": verification.get("result"),
                    "verifier_reason": verification.get("reason"),
                    "final_disposition": final,
                }
            )
        admitted.append(updated)
    path.write_text(json.dumps(admitted, indent=2) + "\n")
    (workspace / "05_adjudication_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    return audit
