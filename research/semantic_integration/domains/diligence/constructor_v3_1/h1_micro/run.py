"""Frozen H1 micro-benchmark. Does not regenerate Probe A or v3 packets."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[5]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.diligence.constructor_v3_1.runtime.negative_closure import (
    evaluate_distinct,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    all_oracle_pairs,
    pair_key,
)

PROBE_A = REPO / "research/semantic_integration/domains/diligence/semantic_proof_benchmark_v1"
A1 = PROBE_A / "strategies" / "a1_single"
PACKETS = PROBE_A / "apparatus" / "packets"
V3_T1 = (
    REPO
    / "research/semantic_integration/domains/diligence/constructor_v3/axis_d/trials/T1/passes/p5/workspace_snapshot"
)
V3_T1_PACKETS = (
    REPO
    / "research/semantic_integration/domains/diligence/constructor_v3/axis_d/trials/T1/passes/p4/workspace_snapshot/04_packets"
)


def _load(path: Path):
    return json.loads(path.read_text())


def a1_r01(oid: str) -> dict:
    return _load(A1 / "R01" / oid / "row.json")


def cases() -> list[dict]:
    oracle = all_oracle_pairs()
    out = []

    def add(*, case_id, packet, proposed, claim, evidence, source, oracle_label):
        left = packet.get("left") or (packet.get("values") or {}).get("left")
        right = packet.get("right") or (packet.get("values") or {}).get("right")
        if not left and isinstance(packet.get("selected_observations"), list):
            cand = {}
        else:
            cand = {"left": left, "right": right}
        pair = pair_key(str(left), str(right)) if left and right else None
        out.append(
            {
                "case_id": case_id,
                "source": source,
                "oracle": oracle_label or (oracle.get(pair) if pair else None),
                "proposed": proposed,
                "support_claim": claim,
                "grounding": evidence,
                "packet": packet,
                "candidate": cand,
            }
        )

    for oid, label in (("id-15", "DISTINCT"), ("id-16", "DISTINCT"), ("id-17", "UNRESOLVED"), ("id-18", "UNRESOLVED")):
        packet = _load(PACKETS / f"{oid}.json")
        row = a1_r01(oid)
        add(
            case_id=f"a1-{oid}",
            packet=packet,
            proposed=row["proposed_disposition"],
            claim=row.get("support_claim") or "",
            evidence=row.get("supporting_evidence") or [],
            source="probe_a_a1_r01",
            oracle_label=row["oracle"],
        )

    t1 = _load(V3_T1 / "05_dispositions.json")
    target = None
    for row in t1:
        values = row.get("values") or {}
        if str(values.get("right") or "") == "registry:2019-0008841" and "Northbridge Analytics Inc." in str(
            values.get("left") or ""
        ):
            target = row
            break
    packet_id = target["obligation_id"] if target else ""
    packet_path = V3_T1_PACKETS / f"{packet_id}.json"
    if target and packet_path.exists():
        add(
            case_id="v3-t1-northbridge-wyoming",
            packet=_load(packet_path),
            proposed=target.get("original_disposition") or target.get("disposition"),
            claim=target.get("support_claim") or "",
            evidence=target.get("supporting_evidence") or [],
            source="constructor_v3_t1",
            oracle_label="UNRESOLVED",
        )
    elif target:
        add(
            case_id="v3-t1-northbridge-wyoming",
            packet={"obligation_id": packet_id, "selected_observations": target.get("supporting_evidence") or []},
            proposed=target.get("original_disposition") or target.get("disposition"),
            claim=target.get("support_claim") or "",
            evidence=target.get("supporting_evidence") or [],
            source="constructor_v3_t1",
            oracle_label="UNRESOLVED",
        )
    return out


def apply_gate(proposed: str, gate_result: str) -> str:
    if proposed != "DISTINCT":
        return proposed
    if gate_result == "SUPPORTED_DISTINCT":
        return "DISTINCT"
    return "UNRESOLVED"


def run() -> dict:
    oracle = all_oracle_pairs()
    rows = []
    for case in cases():
        proposed = str(case["proposed"] or "").upper()
        baseline = proposed
        gate = None
        if proposed == "DISTINCT":
            gate = evaluate_distinct(
                candidate=case["candidate"],
                packet=case["packet"],
                support_claim=case["support_claim"],
                grounding=case["grounding"],
            )
            final = apply_gate(proposed, str(gate.get("result") or ""))
        else:
            final = proposed
        pair = pair_key(str(case["candidate"].get("left") or ""), str(case["candidate"].get("right") or ""))
        want = case["oracle"] or oracle.get(pair)
        rows.append(
            {
                "case_id": case["case_id"],
                "source": case["source"],
                "oracle": want,
                "baseline": baseline,
                "final": final,
                "gate": gate,
                "downgraded": baseline == "DISTINCT" and final == "UNRESOLVED",
                "unsupported_distinct": want == "UNRESOLVED" and final == "DISTINCT",
                "correct_distinct_downgraded": want == "DISTINCT" and baseline == "DISTINCT" and final == "UNRESOLVED",
                "unresolved_preserved": want == "UNRESOLVED" and final == "UNRESOLVED",
            }
        )
    distinct_oracle = [r for r in rows if r["oracle"] == "DISTINCT"]
    unresolved_oracle = [r for r in rows if r["oracle"] == "UNRESOLVED"]
    summary = {
        "n": len(rows),
        "unsupported_distinct_baseline": sum(1 for r in rows if r["oracle"] == "UNRESOLVED" and r["baseline"] == "DISTINCT"),
        "unsupported_distinct_gated": sum(1 for r in rows if r["unsupported_distinct"]),
        "distinct_recall_baseline": (
            sum(1 for r in distinct_oracle if r["baseline"] == "DISTINCT") / len(distinct_oracle)
            if distinct_oracle
            else None
        ),
        "distinct_recall_gated": (
            sum(1 for r in distinct_oracle if r["final"] == "DISTINCT") / len(distinct_oracle)
            if distinct_oracle
            else None
        ),
        "unresolved_preservation_gated": (
            sum(1 for r in unresolved_oracle if r["final"] == "UNRESOLVED") / len(unresolved_oracle)
            if unresolved_oracle
            else None
        ),
        "distinct_downgraded": sum(1 for r in rows if r["downgraded"]),
        "correct_distinct_downgraded": sum(1 for r in rows if r["correct_distinct_downgraded"]),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    payload = {"summary": summary, "rows": rows}
    dest = ROOT / "results.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


if __name__ == "__main__":
    print(json.dumps(run()["summary"], indent=2))
