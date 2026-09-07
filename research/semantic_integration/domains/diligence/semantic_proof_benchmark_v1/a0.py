"""A0: import frozen Constructor v2 AXIS A audits. Do not rerun."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.apparatus import (
    packet_path,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import (
    AXIS_A,
    STRATEGIES,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.scoring import (
    oracle_pairs,
    score_row,
    write_strategy_scores,
)


def import_a0() -> dict:
    oracle = oracle_pairs()
    rows = []
    trials = sorted((AXIS_A / "trials").glob("T*"))
    for trial in trials:
        audit = json.loads((trial / "audit.json").read_text())
        for item in audit:
            oid = str(item.get("packet") or "")
            packet = json.loads(packet_path(oid).read_text()) if packet_path(oid).exists() else {}
            proposed = str(item.get("initial_disposition") or "UNRESOLVED").upper()
            final = str(item.get("final_disposition") or "UNRESOLVED").upper()
            row = {
                "strategy": "a0_v2",
                "trial": trial.name,
                "obligation_id": oid,
                "candidate": item.get("candidate"),
                "proposed_disposition": proposed,
                "final_disposition": final,
                "supporting_evidence": item.get("support_evidence"),
                "support_claim": item.get("support_claim"),
                "verifier_result": item.get("verifier_result"),
                "proof_size": 1,
                "proof_valid": True,
                "isolation_leaks": [],
                "source": "frozen_constructor_v2_axis_a",
            }
            rows.append(score_row(row, packet, oracle))
    dest = STRATEGIES / "a0_v2"
    payload = write_strategy_scores("a0_v2", rows, dest)
    (dest / "source.json").write_text(
        json.dumps({"imported_from": str(AXIS_A / "results.json"), "n_rows": len(rows)}, indent=2)
        + "\n"
    )
    return payload
