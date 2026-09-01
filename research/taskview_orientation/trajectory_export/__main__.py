"""CLI: export sealed Stage 1 v0.1 trajectories. Zero participant inference."""

from __future__ import annotations

import json

from research.taskview_orientation.trajectory_export.export import run


def main() -> None:
    receipt = run()
    print(
        json.dumps(
            {
                "campaign_id": receipt["campaign_id"],
                "participant_inference_calls": receipt["participant_inference_calls"],
                "source_episode_ids": receipt["source_episode_ids"],
                "export_hashes": receipt["export_hashes"],
                "tool_call_counts": receipt["tool_call_counts"],
                "model_visible_tool_result_byte_totals": receipt[
                    "model_visible_tool_result_byte_totals"
                ],
                "integrity_all_pass": receipt["integrity_all_pass"],
                "integrity_check_results": receipt["integrity_check_results"],
                "receipt_path": receipt["receipt_path"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    if not receipt["integrity_all_pass"]:
        raise SystemExit("integrity checks failed")


if __name__ == "__main__":
    main()
