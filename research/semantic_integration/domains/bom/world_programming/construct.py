"""Construct a disposable experimental World for the programming-substrate benchmark.

Copies C1 through existing compile_c1, records mechanical origins, then copies the
already-frozen C2 ACCEPT judgments into the new World.  Does not mutate sealed
artifacts, does not run C2, and does not load C0.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.domains.bom.compiler import compile_c1
from research.semantic_integration.domains.bom.operational_frontier.generate import (
    demanded_cases,
    generate_obligations,
)
from research.semantic_integration.harness.c2 import insert_acceptance


BOM_DOMAIN = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[5]
CAMPAIGN_RESULTS = BOM_DOMAIN / "c2" / "results"
PACKET_DIR = REPO / "research/taskview_bom_scaling/c2/packets"
ADJUDICATIONS = (
    CAMPAIGN_RESULTS / "adjudication-001.json",
    CAMPAIGN_RESULTS / "adjudication-002.json",
)


@dataclass
class ExperimentalWorld:
    world: SemanticWorld
    obligations: list[dict[str, Any]]
    demanded: list[dict[str, str]]


def _backfill_mechanical_origins(world: SemanticWorld) -> None:
    for row in world.query("SELECT assertion_id, origin FROM _tv_assertions"):
        if row["origin"] == "DERIVED":
            continue
        if row["assertion_id"] not in world._origins:
            world._origins[row["assertion_id"]] = ConstructionOrigin.MECHANICAL.value
    world._persist_origins()


def _load_frozen_acceptances() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    packets = {
        tuple(json.loads(path.read_text(encoding="utf-8"))["candidate_assertion"]["tuple"]): json.loads(
            path.read_text(encoding="utf-8")
        )
        for path in sorted(PACKET_DIR.glob("packet-*.json"))
    }
    pairs: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for path in ADJUDICATIONS:
        result_doc = json.loads(path.read_text(encoding="utf-8"))
        if result_doc.get("result", {}).get("decision") != "ACCEPT":
            continue
        key = tuple(result_doc["candidate_assertion"]["tuple"])
        pairs.append((packets[key], result_doc["result"]))
    return pairs


def construct_experimental_world(db_path: Path) -> ExperimentalWorld:
    compilation = compile_c1(db_path)
    world = SemanticWorld.wrap(
        compilation.view, world_id="bom-world-programming-s1"
    )
    _backfill_mechanical_origins(world)
    for packet, result in _load_frozen_acceptances():
        insert_acceptance(world, packet, result)
    obligations = generate_obligations(world.taskview)
    demanded = demanded_cases(world.taskview)
    return ExperimentalWorld(
        world=world, obligations=obligations, demanded=demanded
    )
