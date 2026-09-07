"""Record sealed input hashes. Do not mutate priors."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.materialize import sha256_file
from research.semantic_integration.domains.npdes.end_to_end_programmability_v0.paths import (
    ANATOMY,
    FROZEN,
    OBLIGATION,
    PF_CONSTRUCTION,
    PF_JUDGMENT,
    PF_PROPOSAL,
    PF_T1_DELTA,
    T5_CONSTRUCTION,
    T5_SOURCE,
    T5_WORLD_API,
    WD_CONSTRUCTION,
    WD_JUDGMENT,
    WD_PROPOSAL,
)


def freeze_inputs() -> dict:
    files = {
        "t5_construction.py": T5_CONSTRUCTION,
        "t5_source.py": T5_SOURCE,
        "t5_world_api.py": T5_WORLD_API,
        "t1_when_discharging_construction.py": WD_CONSTRUCTION,
        "t1_when_discharging_proposal.json": WD_PROPOSAL,
        "t1_when_discharging_judgment.json": WD_JUDGMENT,
        "t3_pass_fail_construction.py": PF_CONSTRUCTION,
        "t3_pass_fail_proposal.json": PF_PROPOSAL,
        "t3_pass_fail_judgment.json": PF_JUDGMENT,
        "t1_pass_fail_dry_run_delta.json": PF_T1_DELTA,
        "obligation_master_report": OBLIGATION / "reports" / "obligation_targeted_resolution_v1.md",
        "anatomy_master_report": ANATOMY / "reports" / "semantic_spine_anatomy_v1.md",
        "pfps_master_report": Path(T5_CONSTRUCTION).parents[3] / "reports" / "purpose_first_python_spine_v1.md",
    }
    hashes = {name: sha256_file(path) for name, path in files.items()}
    payload = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "draft_spine": "purpose_first_python_spine_v1/T5",
        "when_discharging": "obligation_targeted_resolution_v1/arm_b/T1/when_discharging",
        "pass_fail": "obligation_targeted_resolution_v1/arm_b/T3/pass_fail",
        "pass_fail_selection_reason": (
            "T1 pass/fail disposable apply completed but materialized 0 binary_pass_fail_* rows "
            "(LIMIT_VALUE_STANDARD_UNITS=='9A'). T2 crashed. T3 materialized 8 pass_fail_outcome_reporting "
            "rows. State C uses T3 because this probe tests application behavior over admitted semantic state."
        ),
        "state_d": "skipped: prior parent/child admission mismatch; not required",
        "hashes": hashes,
    }
    FROZEN.mkdir(parents=True, exist_ok=True)
    (FROZEN / "input_hashes.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload
