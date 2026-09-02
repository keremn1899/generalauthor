"""Evaluator-side causal substitutions. These are not constructor successes."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.evaluator import (
    load_json,
    score_purpose_a,
    score_purpose_b,
    score_purpose_c,
)
from research.semantic_integration.domains.diligence.pass_localization.gold_derive import (
    write_outputs,
)
from research.semantic_integration.domains.diligence.pass_localization.pairs import (
    all_oracle_pairs,
    load_dispositions,
    pair_from_obj,
    pair_key,
)
from research.semantic_integration.domains.diligence.pass_localization.workspaces import (
    REPO_ROOT,
    TRIALS,
)

HIDDEN = Path(__file__).resolve().parent.parent / "hidden"
DELAWARE = pair_key("billing:Northbridge Analytics Inc.", "registry:3840192")
ROOT = Path(__file__).resolve().parent


def _score_payloads(a: dict | None, b: dict | None, c: dict | None) -> dict[str, Any]:
    return {
        "A": score_purpose_a(a, load_json(HIDDEN / "expected" / "purpose_a.json")),
        "B": score_purpose_b(b, load_json(HIDDEN / "expected" / "purpose_b.json")),
        "C": score_purpose_c(c, load_json(HIDDEN / "expected" / "purpose_c.json")),
    }


def _score_dir(dest: Path) -> dict[str, Any]:
    return _score_payloads(
        load_json(dest / "purpose_ir" / "a" / "output.json") or load_json(dest / "08_outputs" / "a.json"),
        load_json(dest / "purpose_ir" / "b" / "output.json") or load_json(dest / "08_outputs" / "b.json"),
        load_json(dest / "purpose_ir" / "c" / "output.json") or load_json(dest / "08_outputs" / "c.json"),
    )


def _identity_relation_name(rows: list[dict]) -> str:
    names = [
        str(row.get("relation"))
        for row in rows
        if pair_from_obj(row) is not None
        and str(row.get("disposition", "")).upper() in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}
    ]
    return names[0] if names else "entity_identity_judgment"


def patch_dispositions(rows: list[dict], replacements: dict[tuple[str, str], str]) -> list[dict]:
    patched = [dict(row) for row in rows]
    seen: set[tuple[str, str]] = set()
    relation = _identity_relation_name(patched)
    for row in patched:
        pair = pair_from_obj(row)
        if pair is None or pair not in replacements:
            continue
        disp = str(row.get("disposition", "")).upper()
        if disp not in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED", "ACCEPT", "REJECT"}:
            continue
        if disp in {"ACCEPT", "REJECT"} and pair_from_obj(row.get("values")) is None:
            continue
        if disp in {"SAME_ENTITY", "DISTINCT", "UNRESOLVED"}:
            row["disposition"] = replacements[pair]
            seen.add(pair)
    for pair, disp in replacements.items():
        if pair in seen:
            continue
        left, right = pair
        patched.append(
            {
                "obligation_id": f"oracle:{left}|{right}",
                "relation": relation,
                "values": {"left": left, "right": right},
                "disposition": disp,
                "grounding": [{"source_path": "hidden-oracle-substitution", "location": "evaluator"}],
                "rationale": "evaluator identity substitution",
            }
        )
    return patched


def assemble_replay(trial: int, dest: Path, dispositions: list[dict]) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    world_src = TRIALS / f"T{trial}" / "passes" / "p6" / "workspace_snapshot" / "06_world" / "world.sqlite"
    derive_src = (
        TRIALS
        / f"T{trial}"
        / "passes"
        / "p7"
        / "workspace_snapshot"
        / "construction"
        / "derivations"
        / "derive_purposes.py"
    )
    if not world_src.exists() or not derive_src.exists():
        raise FileNotFoundError(f"T{trial} missing world or derive script")
    (dest / "06_world").mkdir()
    shutil.copy2(world_src, dest / "06_world" / "world.sqlite")
    (dest / "world").mkdir()
    shutil.copy2(world_src, dest / "world" / "world.sqlite")
    (dest / "construction" / "derivations").mkdir(parents=True)
    shutil.copy2(derive_src, dest / "construction" / "derivations" / "derive_purposes.py")
    (dest / "05_dispositions.json").write_text(json.dumps(dispositions, indent=2) + "\n")
    tv = dest / "taskview"
    tv.mkdir()
    src_tv = REPO_ROOT / "taskview"
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        shutil.copy2(src_tv / name, tv / name)
    return dest


def run_participant_derive(replay: Path) -> dict[str, Any]:
    script = replay / "construction" / "derivations" / "derive_purposes.py"
    env_pythonpath = str(replay)
    completed = subprocess.run(
        [sys.executable, str(script)],
        cwd=replay,
        text=True,
        capture_output=True,
        check=False,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": env_pythonpath},
    )
    return {
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[-2000:],
        "stderr": (completed.stderr or "")[-2000:],
    }


def _load_p5(trial: int) -> list[dict]:
    return load_dispositions(
        TRIALS / f"T{trial}" / "passes" / "p5" / "workspace_snapshot" / "05_dispositions.json"
    )


def intervention_p5(trial: int, dest: Path) -> dict[str, Any]:
    try:
        patched = patch_dispositions(_load_p5(trial), all_oracle_pairs())
        assemble_replay(trial, dest, patched)
        ran = run_participant_derive(dest)
        if ran["returncode"] != 0:
            return {"ok": False, "reason": "derive failed", "run": ran}
        return {"ok": True, "mode": "participant_derive_after_oracle_p5", "scores": _score_dir(dest)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}


def intervention_p7(trial: int, dest: Path) -> dict[str, Any]:
    try:
        world = TRIALS / f"T{trial}" / "passes" / "p6" / "workspace_snapshot" / "06_world" / "world.sqlite"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(world, dest / "world.sqlite")
        write_outputs(dest / "world.sqlite", dest / "08_outputs")
        return {"ok": True, "mode": "gold_derive_on_participant_world", "scores": _score_dir(dest)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}


def intervention_p5_p7(trial: int, dest: Path) -> dict[str, Any]:
    """Oracle identity plus evaluator derivation over participant mechanical World."""
    try:
        from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
            build_certified_world,
        )

        dest.mkdir(parents=True, exist_ok=True)
        world = dest / "world.sqlite"
        build_certified_world(world)
        write_outputs(world, dest / "08_outputs")
        return {
            "ok": True,
            "mode": "certified_world_gold_derive",
            "scores": _score_dir(dest),
            "note": "P5+P7 substitution uses evaluator-certified identity and clauses; mechanical source facts match the frozen fixture.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}


def intervention_delaware(trial: int, dest: Path) -> dict[str, Any]:
    try:
        patched = patch_dispositions(_load_p5(trial), {DELAWARE: "UNRESOLVED"})
        assemble_replay(trial, dest, patched)
        ran = run_participant_derive(dest)
        if ran["returncode"] != 0:
            return {"ok": False, "reason": "derive failed", "run": ran}
        orig = TRIALS / f"T{trial}" / "passes" / "p8" / "workspace_snapshot"
        return {
            "ok": True,
            "mode": "participant_derive_delaware_unresolved",
            "pair": list(DELAWARE),
            "scores": _score_dir(dest),
            "baseline": _score_payloads(
                load_json(orig / "08_outputs" / "a.json"),
                load_json(orig / "08_outputs" / "b.json"),
                load_json(orig / "08_outputs" / "c.json"),
            ),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "reason": str(exc)}


def run_all_interventions() -> dict[str, Any]:
    root = ROOT / "interventions"
    payload = {}
    for trial in range(1, 6):
        if not (TRIALS / f"T{trial}" / "passes" / "p8" / "agent.json").exists():
            continue
        payload[f"T{trial}"] = {
            "correct_p5": intervention_p5(trial, root / f"T{trial}" / "correct_p5"),
            "correct_p7": intervention_p7(trial, root / f"T{trial}" / "correct_p7"),
            "correct_p5_p7": intervention_p5_p7(trial, root / f"T{trial}" / "correct_p5_p7"),
            "delaware_unresolved": intervention_delaware(trial, root / f"T{trial}" / "delaware"),
        }
    root.mkdir(parents=True, exist_ok=True)
    (root / "results.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload
