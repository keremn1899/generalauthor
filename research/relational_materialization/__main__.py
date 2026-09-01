"""CLI for generating and smoke-running the frozen pilot shape."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generator import write_case
from .model import Arm, Cell, Heterogeneity, Novelty
from .runner import PROTOCOL_VERSION, reference_command, run_case


def cells() -> list[Cell]:
    return [Cell(h, n, r) for h in Heterogeneity for n in Novelty for r in (1, 2, 4, 8)]


def generate(root: Path, seeds: list[int]) -> list[Path]:
    root.mkdir(parents=True, exist_ok=True)
    return [write_case(root, cell, seed) for cell in cells() for seed in seeds]


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent-authored relational-materialization pilot")
    subparsers = parser.add_subparsers(dest="command", required=True)
    generate_parser = subparsers.add_parser("generate", help="generate paired, oracle-scored cases")
    generate_parser.add_argument("--out", type=Path, required=True)
    generate_parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    smoke_parser = subparsers.add_parser("smoke", help="run the deterministic harness smoke test over all pilot cells")
    smoke_parser.add_argument("--out", type=Path, required=True)
    smoke_parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    smoke_parser.add_argument("--timeout", type=int, default=60)
    run_parser = subparsers.add_parser("run", help="run an external agent over generated cases")
    run_parser.add_argument("--cases", type=Path, required=True, help="directory produced by generate")
    run_parser.add_argument("--results", type=Path, required=True)
    run_parser.add_argument("--arm", choices=[arm.value for arm in Arm], required=True)
    run_parser.add_argument("--agent-command", required=True)
    run_parser.add_argument("--timeout", type=int, default=180, help="same total wall-clock budget for every arm")
    args = parser.parse_args()
    if args.command == "generate":
        cases = generate(args.out / "cases", args.seeds)
        print(json.dumps({"generated_cases": len(cases), "cells": [cell.id for cell in cells()]}))
        return
    if args.command == "run":
        case_paths = sorted(path for path in args.cases.iterdir() if (path / "agent").is_dir() and (path / "evaluator" / "oracle.json").is_file())
        records = [run_case(case, Arm(args.arm), args.agent_command, args.results, timeout=args.timeout) for case in case_paths]
        successful = sum(record["workload_success"] == 1.0 and not record["symptoms"] and record["returncode"] == 0 for record in records)
        print(json.dumps({"protocol": PROTOCOL_VERSION, "runs": len(records), "fully_passing": successful}))
        return
    cases = generate(args.out / "cases", args.seeds)
    records = [run_case(case, arm, reference_command(), args.out / "results", timeout=args.timeout)
               for case in cases for arm in Arm]
    successful = sum(record["workload_success"] == 1.0 and not record["symptoms"] and record["returncode"] == 0 for record in records)
    summary = {"protocol": PROTOCOL_VERSION, "runs": len(records), "fully_passing": successful}
    (args.out / "results" / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
