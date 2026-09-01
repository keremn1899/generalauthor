"""CLI for the compiled-projection experiment. Default: deterministic preflight."""

from __future__ import annotations

import argparse
import json

from research.taskview_orientation.compiled_projection.campaign import (
    LiveInferenceBlocked,
    run_campaign,
)
from research.taskview_orientation.compiled_projection.preflight import run_preflight


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TaskView compiled decision-projection experiment"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="preflight",
        choices=("preflight", "run", "report"),
    )
    args = parser.parse_args()
    if args.command == "preflight":
        print(json.dumps(run_preflight(), indent=2, sort_keys=True))
        return
    if args.command == "report":
        from research.taskview_orientation.compiled_projection.campaign import RESULTS_ROOT
        from research.taskview_orientation.compiled_projection.report import write_report

        print(json.dumps(write_report(RESULTS_ROOT), indent=2, sort_keys=True))
        return
    try:
        print(json.dumps(run_campaign(), indent=2, sort_keys=True))
    except LiveInferenceBlocked as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    main()
