"""AXIS B: relation-contract integrity on the certified World and projected purposes."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.runtime.projector import (
    write_purpose_outputs,
)
from research.semantic_integration.domains.diligence.constructor_v2.runtime.validators import (
    axis_b_payload,
)
from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
    build_certified_world,
)

ROOT = Path(__file__).resolve().parent


def run_axis_b(tmp: Path | None = None) -> dict:
    dest = tmp or (ROOT / "axis_b")
    dest.mkdir(parents=True, exist_ok=True)
    world = dest / "world.sqlite"
    build_certified_world(world)
    outputs = write_purpose_outputs(world, dest / "08_outputs")
    payload = axis_b_payload(world, outputs["c"]["dependencies"])
    payload["axis"] = "B"
    (dest / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload


if __name__ == "__main__":
    print(json.dumps(run_axis_b(), indent=2, sort_keys=True))
