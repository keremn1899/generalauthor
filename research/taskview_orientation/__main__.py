from __future__ import annotations

import argparse
import json
from pathlib import Path

from research.taskview_orientation.freeze import freeze_apparatus
from research.taskview_orientation.runner import EpisodeRunner, scripted_session_factory


def main() -> None:
    parser = argparse.ArgumentParser(description="TaskView orientation Stage 0 apparatus")
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze_parser = subparsers.add_parser("freeze")
    freeze_parser.add_argument("--replace", action="store_true")
    dry_parser = subparsers.add_parser("dry-run")
    dry_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    if args.command == "freeze":
        print(json.dumps(freeze_apparatus(replace=args.replace), indent=2, sort_keys=True))
        return
    runner = EpisodeRunner(session_factory=scripted_session_factory)
    records = [
        runner.run(arm=arm, replicate=0, output_root=args.out / arm.lower())
        for arm in ("RAW", "TASKVIEW")
    ]
    print(json.dumps(records, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

