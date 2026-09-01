"""Frozen block order and reassembly classification for compiled-projection."""

from __future__ import annotations

import json
import random
from functools import lru_cache
from typing import Any

from research.taskview_orientation.compiled_projection import (
    BLOCK_COUNT,
    CAMPAIGN_ID,
    CONDITIONS,
    FROZEN_DIR,
    SEED,
)


def load_reassembly() -> dict[str, Any]:
    return json.loads((FROZEN_DIR / "reassembly.json").read_text(encoding="utf-8"))


def load_block_order() -> dict[str, Any]:
    return json.loads((FROZEN_DIR / "block_order.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def reassembly() -> dict[str, Any]:
    return load_reassembly()


def generate_block_order(seed: int = SEED) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {}
    for block in range(1, BLOCK_COUNT + 1):
        order = list(CONDITIONS)
        random.Random(seed + 1000 * block).shuffle(order)
        blocks[str(block)] = order
    return blocks


def block_conditions(block: int) -> tuple[str, ...]:
    return tuple(load_block_order()["blocks"][str(block)])


def episode_matrix() -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    ordinal = 0
    for block in range(1, BLOCK_COUNT + 1):
        for condition in block_conditions(block):
            ordinal += 1
            episodes.append(
                {
                    "ordinal": ordinal,
                    "block": block,
                    "condition": condition,
                    "episode_id": f"{CAMPAIGN_ID}-b{block}-{condition.lower()}",
                    "arm": "TASKVIEW",
                    "replicate": block,
                }
            )
    return episodes
