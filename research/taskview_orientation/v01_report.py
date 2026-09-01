"""Analyze the sealed v0.1 repeat under separate frozen criteria."""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from research.taskview_orientation.report import DIMENSION_FIELD_MAP, _dimension_scores, _episode_summary
from research.taskview_orientation.v01_authorize import AUTHORIZED_MANIFEST_PATH


def analyze(root: Path, manifest_path: Path = AUTHORIZED_MANIFEST_PATH) -> dict[str, Any]:
    seal = json.loads((root / "campaign_seal.json").read_text(encoding="utf-8"))
    if seal.get("status") != "SEALED" or seal.get("valid") is not True:
        raise RuntimeError("campaign is not valid and sealed")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    episodes = [
        _episode_summary(root, episode)
        for episode in manifest["stage1"]["episodes"]
    ]
    by_key = {(item["arm"], item["replicate"]): item for item in episodes}
    pairs = []
    for replicate in range(1, 5):
        raw = by_key[("RAW", replicate)]
        treatment = by_key[("TASKVIEW", replicate)]
        reduction = (
            (raw["O_post"] - treatment["O_post"]) / raw["O_post"]
            if raw["O_post"]
            else None
        )
        net_delta = treatment["net_orientation_bytes"] - raw["O_post"]
        pairs.append(
            {
                "replicate": replicate,
                "RAW_O_post": raw["O_post"],
                "TASKVIEW_O_post": treatment["O_post"],
                "paired_O_post_reduction": reduction,
                "directional_O_post_win": treatment["O_post"] < raw["O_post"],
                "RAW_orientation_cost": raw["O_post"],
                "TASKVIEW_repository_orientation": treatment["O_post"],
                "TASKVIEW_visible_consumption": treatment["taskview_visible_bytes"],
                "TASKVIEW_net_orientation": treatment["net_orientation_bytes"],
                "net_orientation_delta": net_delta,
                "economic_win": net_delta < 0,
                "RAW_local_source_inspection_rate": raw["local_source_inspection_rate"],
                "TASKVIEW_local_source_inspection_rate": treatment["local_source_inspection_rate"],
                "RAW_local_correctness": raw["dimensions"]["local_implementation_semantics"],
                "TASKVIEW_local_correctness": treatment["dimensions"]["local_implementation_semantics"],
                "TASKVIEW_consumption": {
                    "describe_catalog": treatment["describe_catalog_calls"],
                    "describe_relation": treatment["describe_relation_calls"],
                    "describe_why": treatment["describe_why_calls"],
                    "query_sql": treatment["taskview_calls_by_operation"].get("query_sql", 0),
                    "assertion": treatment["taskview_calls_by_operation"].get("assertion", 0),
                    "rerun": treatment["taskview_calls_by_operation"].get("rerun", 0),
                    "visible_bytes_by_variant": treatment["taskview_visible_bytes_by_variant"],
                },
            }
        )
    reductions = [pair["paired_O_post_reduction"] for pair in pairs]
    net_deltas = [pair["net_orientation_delta"] for pair in pairs]
    o_post_wins = sum(pair["directional_O_post_win"] for pair in pairs)
    economic_wins = sum(pair["economic_win"] for pair in pairs)
    raw_local = statistics.mean(
        item["dimensions"]["local_implementation_semantics"]["rate"]
        for item in episodes if item["arm"] == "RAW"
    )
    treatment_local = statistics.mean(
        item["dimensions"]["local_implementation_semantics"]["rate"]
        for item in episodes if item["arm"] == "TASKVIEW"
    )
    treatment_inspection = statistics.mean(
        item["local_source_inspection_rate"]
        for item in episodes if item["arm"] == "TASKVIEW"
    )
    median_reduction = statistics.median(reductions)
    median_net_delta = statistics.median(net_deltas)
    orientation_pass = (
        median_reduction >= 0.30
        and o_post_wins >= 3
        and treatment_local >= raw_local
        and treatment_inspection >= 0.80
    )
    orientation_result = "PASS" if orientation_pass else "FAIL"
    economics_pass = (
        median_net_delta < 0
        and economic_wins >= 3
        and o_post_wins >= 3
        and treatment_inspection >= 0.80
    )
    economics_result = "PASS" if economics_pass else "FAIL"
    return {
        "campaign_valid": True,
        "campaign_id": seal["campaign_id"],
        "manifest_sha256": seal["manifest_sha256"],
        "episodes": episodes,
        "matched_pairs": pairs,
        "aggregate": {
            "median_paired_O_post_reduction": median_reduction,
            "O_post_directional_wins": o_post_wins,
            "median_net_orientation_delta": median_net_delta,
            "net_orientation_directional_wins": economic_wins,
            "RAW_local_correctness": raw_local,
            "TASKVIEW_local_correctness": treatment_local,
            "TASKVIEW_local_source_inspection_rate": treatment_inspection,
            "post_phase1_repository_bytes_by_phase": {
                item["campaign_episode_id"]: item["post_phase1_repository_bytes_by_phase"]
                for item in episodes
            },
        },
        "orientation_mechanism_result": orientation_result,
        "net_economics_result": economics_result,
        "known_oracle_limitations": manifest["known_oracle_limitations"],
        "dimension_field_map": DIMENSION_FIELD_MAP,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = analyze(args.results)
    if args.out:
        args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
