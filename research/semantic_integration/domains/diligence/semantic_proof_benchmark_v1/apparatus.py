"""Copy frozen AXIS A packets into Probe A apparatus. Do not regenerate from sources."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import (
    APPARATUS,
    APPARATUS_SRC,
    MANIFEST,
    V2,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def freeze_apparatus() -> dict[str, str]:
    src_packets = APPARATUS_SRC / "packets"
    dest_packets = APPARATUS / "packets"
    dest_packets.mkdir(parents=True, exist_ok=True)
    v2_manifest = json.loads((V2 / "experiment_manifest.json").read_text())
    expected = v2_manifest["axis_a_packet_fingerprints"]
    fingerprints = {}
    for name, want in expected.items():
        src = src_packets / name
        dest = dest_packets / name
        shutil.copy2(src, dest)
        got = sha256_file(dest)
        if got != want:
            raise RuntimeError(f"packet fingerprint mismatch {name}: {got} != {want}")
        fingerprints[name] = got
    shutil.copy2(APPARATUS_SRC / "identity_contract.json", APPARATUS / "relation_contract.json")
    shutil.copy2(APPARATUS_SRC / "obligations.json", APPARATUS / "obligations.json")
    (APPARATUS / "README.md").write_text(
        "Frozen AXIS A identity packets. No gold dispositions. Not regenerated.\n",
        encoding="utf-8",
    )
    return fingerprints


def load_obligations() -> list[dict]:
    return json.loads((APPARATUS / "obligations.json").read_text())


def packet_path(obligation_id: str) -> Path:
    return APPARATUS / "packets" / f"{obligation_id}.json"
