"""Resume ordinary trials, then evaluator interventions and diagnostics. No constructor repairs."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.diligence.pass_localization.campaign import run_all_trials
from research.semantic_integration.domains.diligence.pass_localization.diagnostics import (
    run_all_p7_certified,
    run_d_world_only,
)
from research.semantic_integration.domains.diligence.pass_localization.interventions import (
    run_all_interventions,
)
from research.semantic_integration.domains.diligence.pass_localization.report import write_report
from research.semantic_integration.domains.diligence.pass_localization.score_passes import score_all


def main() -> None:
    ordinary_path = Path(
        "research/semantic_integration/domains/diligence/pass_localization/campaign_ordinary.json"
    )
    if ordinary_path.exists():
        ordinary = json.loads(ordinary_path.read_text())
    else:
        ordinary = run_all_trials()
    scores = score_all()
    (Path("research/semantic_integration/domains/diligence/pass_localization") / "ordinary_scores.json").write_text(
        json.dumps(scores, indent=2, sort_keys=True) + "\n"
    )
    interventions_path = Path(
        "research/semantic_integration/domains/diligence/pass_localization/interventions/results.json"
    )
    if interventions_path.exists():
        interventions = json.loads(interventions_path.read_text())
    else:
        interventions = run_all_interventions()
    d_world = run_d_world_only()
    p7c = run_all_p7_certified()
    report = write_report()
    print(
        json.dumps(
            {
                "ordinary": ordinary,
                "n_scored_trials": len(scores),
                "d_world_only": d_world,
                "p7_certified_trials": list(p7c),
                "report_pass_keys": list((report.get("ordinary_scores") or {})),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
