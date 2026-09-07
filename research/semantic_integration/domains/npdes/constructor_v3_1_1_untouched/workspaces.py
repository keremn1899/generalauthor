"""Workspaces for untouched NPDES Constructor v3.1.1 ordinary trials."""

from __future__ import annotations

import shutil
from pathlib import Path

from research.semantic_integration.domains.npdes.constructor_v3_1_1_untouched.prompts import (
    PASS_ORDER,
    PROMPTS,
)

ROOT = Path(__file__).resolve().parent
NPDES = ROOT.parent
REPO = ROOT.parents[4]
SOURCES = NPDES / "fixture" / "participant_sources" / "sources"
PURPOSES = NPDES / "fixture" / "participant_sources" / "purposes"
KERNEL = NPDES / "kernel_assets" / "KERNEL.md"
TASKVIEW_SRC = REPO / "taskview"
TRIALS = ROOT / "trials"

PASS_OUTPUTS = {
    "p0": ["00_intention_contract.json"],
    "p1": ["01_vocabulary.json", "01_abi_completeness.json"],
    "p2": ["02_mechanical_world/world.sqlite", "02_mechanical_report.json"],
    "p3": ["03_obligations.json"],
    "p4": ["04_packets"],
    "p5": ["05_dispositions.json", "05_adjudication_audit.json"],
    "p6": ["06_admission.json", "06_world/world.sqlite", "06_provenance.json"],
    "p7": ["07_derivations.json", "construction/derivations/derive_purposes.py"],
    "p8": [
        "08_outputs/a.json",
        "08_outputs/b.json",
        "08_outputs/c.json",
        "08_abi_completeness.json",
        "purpose_ir/a/output.json",
        "purpose_ir/b/output.json",
        "purpose_ir/c/output.json",
    ],
}


def copy_taskview(destination: Path) -> None:
    dest_tv = destination / "taskview"
    dest_tv.mkdir(parents=True, exist_ok=True)
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        src = TASKVIEW_SRC / name
        if src.exists():
            shutil.copy2(src, dest_tv / name)


def copy_visible_sources(destination: Path) -> None:
    shutil.copytree(SOURCES, destination / "sources")
    purposes = destination / "purposes"
    purposes.mkdir()
    for name in ("visible_a.md", "visible_b.md", "visible_c.md"):
        shutil.copy2(PURPOSES / name, purposes / name)
    shutil.copy2(KERNEL, destination / "KERNEL.md")
    copy_taskview(destination)


def seed_ordinary_workspace(destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    copy_visible_sources(destination)
    (destination / "README.md").write_text(
        "Constructor v3.1.1 untouched NPDES workspace. Visible sources and purposes A/B/C only.\n",
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
        "01_vocabulary.json",
        "01_abi_completeness.json",
        "06_provenance.json",
        "08_abi_completeness.json",
        "purpose_ir/a/output.json",
        "purpose_ir/b/output.json",
        "purpose_ir/c/output.json",
        "purpose_ir/d/output.json",
        "construction/derivations/derive_purposes.py",
        "00_intention_contract.json",
        "03_obligations.json",
        "07_derivations.json",
    ):
        src = live / extra
        if src.exists() and src.is_file():
            target = dest / extra
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
