"""Freeze three parent obligations and copy sealed prior packets. Evaluator expected splits stay hidden."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from research.semantic_integration.domains.npdes.semantic_refinement_admission_v1.paths import (
    DRAFT_TRIAL,
    EVALUATOR_ONLY,
    FROZEN,
    OBLIGATION_IDS,
    OTR,
    PFPS,
)

STRUCTURED_PARTITIONS = {
    "geometric_mean": {
        "fields": [
            "PARAMETER_CODE",
            "PARAMETER_DESC",
            "DMR_COMMENT_TEXT",
            "STATISTICAL_BASE_TYPE_CODE",
            "LIMIT_FREQ_OF_ANALYSIS_CODE",
            "LIMIT_VALUE_NMBR",
        ],
        "note": "These structured fields exist on the affected permit_limits rows. Partition only if retrieved evidence shows materially different semantic consequences.",
    },
    "empty_numeric_limit": {
        "fields": [
            "LIMIT_VALUE_NMBR",
            "DMR_COMMENT_TEXT",
            "LIMIT_UNIT_DESC",
            "PARAMETER_CODE",
            "STATISTICAL_BASE_CODE",
            "LIMIT_VALUE_TYPE_CODE",
        ],
        "note": "Empty LIMIT_VALUE_NMBR rows are not necessarily one class. Use structured fields plus permit text. Residual unknown is allowed.",
    },
    "document_authority": {
        "fields": ["document_kind", "filename", "permit", "workspace document text"],
        "note": "Filename kind is not hierarchy. Distinguish document-local self-description from a general precedence rule.",
    },
}


def dump(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def expected() -> dict:
    return {
        "geometric_mean": {
            "consequential_split": "TDS-specific geometric-mean reporting vs non-TDS rows carrying TDS-specific comment text",
            "not_gold_names": True,
        },
        "empty_numeric_limit": {
            "possible_children": [
                "ordinary Report/N/A cell",
                "pass/fail special encoding",
                "WHEN DISCHARGING-related empty slot",
                "geometric-mean/reporting slot",
                "residual unknown",
            ],
            "not_required_count": True,
        },
        "document_authority": {
            "levels": [
                "LEVEL 1 document-local self-description",
                "LEVEL 2 kind/corpus-local role in this package",
                "LEVEL 3 general final-permit-outranks-fact-sheet rule",
            ],
            "withhold_level_3_unless_established": True,
        },
    }


def freeze() -> dict:
    FROZEN.mkdir(parents=True, exist_ok=True)
    EVALUATOR_ONLY.mkdir(parents=True, exist_ok=True)
    selected = load(OTR / "frozen" / "selected_obligations.json")
    by_id = {s["obligation_id"]: s for s in selected["obligations"]}
    packets_dir = FROZEN / "prior_packets"
    packets_dir.mkdir(parents=True, exist_ok=True)
    specs = []
    for oid in OBLIGATION_IDS:
        src = by_id[oid]
        packet_src = OTR / "runs" / "arm_b" / "T1" / oid / "PACKET.json"
        shutil.copy2(packet_src, packets_dir / f"{oid}.json")
        host = {
            "obligation_id": src["obligation_id"],
            "requirement_schema": src["requirement_schema"],
            "exact_semantic_question": src["exact_semantic_question"],
            "declared_purposes": src["declared_purposes"],
            "relation_contract": src["relation_contract"],
            "source_field_value": src["source_field_value"],
            "affected_occurrence_count": src["n_occurrences"],
            "representative_examples": (src.get("occurrence_ids") or [])[:6],
            "why_computation_is_blocked": src["why_blocked"],
            "structured_partitions_available": STRUCTURED_PARTITIONS[oid],
            "prior_packet_note": "PRIOR_PACKET.json is a bounded prior retrieval packet, not a gold disposition.",
        }
        specs.append({**host, "occurrence_ids": src.get("occurrence_ids") or []})
    dump(FROZEN / "selected_obligations.json", {"obligations": specs, "host_visible": [{k: s[k] for k in s if k != "occurrence_ids"} for s in specs]})
    dump(
        FROZEN / "baseline.json",
        {
            "draft_trial": DRAFT_TRIAL,
            "construction": str(PFPS / "runs" / DRAFT_TRIAL / "iter1" / "construction.py"),
            "prior_probe": "obligation_targeted_resolution_v1",
            "prior_packets": "frozen/prior_packets from sealed Arm B T1",
        },
    )
    dump(EVALUATOR_ONLY / "expected.json", expected())
    (EVALUATOR_ONLY / "README.md").write_text(
        "Evaluator-only expected distinctions. Never copy into a host workspace. Not GOLD NPDES law.\n",
        encoding="utf-8",
    )
    (FROZEN / "experiment_freeze.md").write_text(
        "\n".join(
            [
                "# Semantic Refinement & Admission Microprobe v1 — freeze",
                "",
                f"Draft spine: sealed {DRAFT_TRIAL}",
                f"Parents: {', '.join(OBLIGATION_IDS)}",
                "Prior packets: sealed OTR Arm B T1 (copied). Host does not see expected.json.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return {"n_selected": len(specs), "ids": list(OBLIGATION_IDS)}


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
