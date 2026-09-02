"""Workspaces for Constructor v2 ordinary trials. P8 is deterministic."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.prompts import PROMPTS
from research.semantic_integration.domains.diligence.constructor_v2.runtime.contracts import (
    PURPOSE_A,
    PURPOSE_B,
    PURPOSE_C,
    PURPOSE_D,
    contract_to_dict,
    IDENTITY_CONTRACT,
)
from research.semantic_integration.domains.diligence.pass_localization.workspaces import (
    copy_visible_sources,
)

ROOT = Path(__file__).resolve().parent
TRIALS = ROOT / "axis_d" / "trials"

PASS_OUTPUTS = {
    "p0": ["00_intention_contract.json"],
    "p1": ["01_vocabulary.json"],
    "p2": ["02_mechanical_world/world.sqlite", "02_mechanical_report.json"],
    "p3": ["03_obligations.json"],
    "p4": ["04_packets"],
    "p5": ["05_dispositions.json", "05_adjudication_audit.json"],
    "p6": ["06_admission.json", "06_world/world.sqlite"],
    "p7": ["07_derivations.json", "construction/derivations/derive_purposes.py"],
    "p8": ["08_outputs/a.json", "08_outputs/b.json", "08_outputs/c.json", "08_outputs/d.json"],
}


def write_contracts(destination: Path) -> None:
    dest = destination / "contracts"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "identity_judgment.json").write_text(
        json.dumps(contract_to_dict(IDENTITY_CONTRACT), indent=2) + "\n"
    )
    for contract in (PURPOSE_A, PURPOSE_B, PURPOSE_C, PURPOSE_D):
        payload = {
            "purpose_id": contract.purpose_id,
            "output_fields": contract.output_fields,
            "identifier_rendering": contract.identifier_rendering,
            "disposition_mapping": contract.disposition_mapping,
            "allowed_kinds": contract.allowed_kinds,
            "row_inclusion": contract.row_inclusion,
            "orientation": contract.orientation,
            "completeness": contract.completeness,
        }
        (dest / f"purpose_{contract.purpose_id.lower()}.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )


def seed_ordinary_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    copy_visible_sources(destination)
    write_contracts(destination)
    (destination / "README.md").write_text(
        "Constructor v2 repair workspace. Visible sources and purposes A/B/C only.\n",
        encoding="utf-8",
    )
    for name in (
        "02_mechanical_world",
        "04_packets",
        "06_world",
        "08_outputs",
        "construction/derivations",
        "purpose_ir/a",
        "purpose_ir/b",
        "purpose_ir/c",
        "purpose_ir/d",
        "world",
        "reports",
        "contracts",
    ):
        (destination / name).mkdir(parents=True, exist_ok=True)


def install_pass_task(destination: Path, pass_id: str) -> None:
    (destination / "PASS_TASK.md").write_text(PROMPTS[pass_id], encoding="utf-8")


def restore_frozen_artifacts(live: Path, sealed_trial: Path, upto_pass: str) -> None:
    from research.semantic_integration.domains.diligence.constructor_v2.prompts import PASS_ORDER

    for prior in PASS_ORDER:
        if prior == upto_pass:
            break
        src = sealed_trial / "passes" / prior / "workspace_snapshot"
        if not src.is_dir():
            continue
        for rel in PASS_OUTPUTS.get(prior, []):
            src_path = src / rel
            if not src_path.exists():
                continue
            dest = live / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if src_path.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(src_path, dest)
            else:
                shutil.copy2(src_path, dest)
        world_src = src / "06_world" / "world.sqlite"
        if prior == "p6" and world_src.exists():
            (live / "world").mkdir(exist_ok=True)
            shutil.copy2(world_src, live / "world" / "world.sqlite")
        mech = src / "02_mechanical_world" / "world.sqlite"
        if prior == "p2" and mech.exists() and not (live / "06_world" / "world.sqlite").exists():
            (live / "world").mkdir(exist_ok=True)
            if not (live / "world" / "world.sqlite").exists():
                shutil.copy2(mech, live / "world" / "world.sqlite")


def snapshot_pass(live: Path, sealed_trial: Path, pass_id: str) -> None:
    dest = sealed_trial / "passes" / pass_id / "workspace_snapshot"
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    for rel in PASS_OUTPUTS.get(pass_id, []):
        src = live / rel
        if not src.exists():
            continue
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, target)
        else:
            shutil.copy2(src, target)
    for extra in (
        "world/world.sqlite",
        "06_world/world.sqlite",
        "02_mechanical_world/world.sqlite",
        "05_dispositions.json",
        "05_adjudication_audit.json",
        "purpose_ir/a/output.json",
        "purpose_ir/b/output.json",
        "purpose_ir/c/output.json",
        "purpose_ir/d/output.json",
        "construction/derivations/derive_purposes.py",
    ):
        src = live / extra
        if src.exists():
            target = dest / extra
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
