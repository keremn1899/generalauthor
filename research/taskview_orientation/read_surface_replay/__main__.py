"""CLI: deterministic TaskView read-surface replay. Zero participant inference."""

from __future__ import annotations

import json

from research.taskview_orientation.read_surface_replay.report import run


def main() -> None:
    result = run()
    print(
        json.dumps(
            {
                "campaign_id": result["campaign_id"],
                "participant_inference_calls": result["participant_inference_calls"],
                "sql_facts": result["sql_facts"],
                "admissions": result["admissions"],
                "safety_all": result["safety"]["all_safe"],
                "tables": result["tables"]["trajectory_preserving"],
                "headroom_label": result["headroom"]["justification"]["label"],
                "headroom_wins": {
                    "modest_25pct": result["headroom"]["justification"]["modest_25pct_wins"],
                    "both_conservative": result["headroom"]["justification"][
                        "both_conservative_wins"
                    ],
                    "harsh_half_breadth": result["headroom"]["justification"][
                        "harsh_half_breadth_wins"
                    ],
                    "fixed_overhead": result["headroom"]["justification"][
                        "fixed_overhead_wins"
                    ],
                },
                "break_even": result["headroom"]["break_even"],
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
