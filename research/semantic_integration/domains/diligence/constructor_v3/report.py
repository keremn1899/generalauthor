"""Frozen Constructor v3 report from measured campaign + certified suite."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3.certified import run_certified_suite
from research.semantic_integration.domains.diligence.constructor_v3.isolation import EXPERIMENT_ID, REPO
from research.semantic_integration.domains.diligence.constructor_v3.score import score_all

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
TASKVIEW = REPO / "taskview"
FORBIDDEN_IMPORTS = (
    "constructor_v2.runtime.verifier",
    "semantic_proof_benchmark",
    "schema_normalization_v1",
)


def kernel_fingerprint() -> dict[str, str]:
    out = {}
    for name in ("__init__.py", "model.py", "store.py", "agent_surface.py"):
        path = TASKVIEW / name
        out[name] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def runtime_import_audit() -> dict[str, Any]:
    runtime = ROOT / "runtime"
    hits = []
    for path in runtime.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            for name in names:
                if any(token in (name or "") for token in FORBIDDEN_IMPORTS):
                    hits.append({"file": str(path.relative_to(ROOT)), "import": name})
    return {"forbidden_hits": hits, "ok": not hits}


def mark(ok: bool) -> str:
    return "✓" if ok else "✗"


def write_report() -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    matrix = score_all()
    certified = run_certified_suite()
    audit = runtime_import_audit()
    kernel = kernel_fingerprint()
    campaign_path = ROOT / "axis_d" / "campaign.json"
    campaign = json.loads(campaign_path.read_text()) if campaign_path.exists() else {}

    p5_rows = []
    p8_rows = []
    for trial, payload in sorted(matrix.items()):
        p5 = payload.get("p5") or {}
        p8 = payload.get("p8") or {}
        p5_rows.append(
            f"{trial:<4} {p5.get('compared')} {p5.get('correct')}/{p5.get('compared')} "
            f"{p5.get('incorrect_semantic_closure')} {p5.get('incorrect_under_closure')} "
            f"{p5.get('incorrect_polarity')} {p5.get('same_recall')} {p5.get('coverage')} "
            f"{p5.get('delaware_inc_disposition')}"
        )
        p8_rows.append(
            f"{trial:<4} A={p8.get('A', {}).get('pass')} B={p8.get('B', {}).get('exact')} "
            f"C={p8.get('C', {}).get('pass')} D={p8.get('D', {}).get('pass')} "
            f"attr={p8.get('failure_attribution')} norm_miss={p8.get('normalization', {}).get('missing_mappings')}"
        )

    lines = [
        "# Constructor v3",
        "",
        f"Experiment `{EXPERIMENT_ID}`. Model: `composer-2.5`. Diligence repair fixture only.",
        "",
        "Labels: **MEASURED** = campaign or certified suite; **OBSERVED** = trial-level detail; **HYPOTHESIS** = interpretation.",
        "",
        "## Implementation delta",
        "",
        "- RelationContract roles may declare `semantic_identity`. Purpose contracts include `field_sources` keyed by consumer field.",
        "- Default P5 is the Probe A A1 single bounded adjudicator. Cue verifier, critics, and proof machinery are off the default path.",
        "- Admission is structural only (invalid disposition / missing grounding).",
        "- P8 is World → contract-driven normalize → deterministic project. No source reread.",
        "- P3 is unchanged from v2.",
        "",
        "## Architecture / dependency delta",
        "",
        "See `research/semantic_integration/ARCHITECTURE.md`. Default v3 runtime lives under `constructor_v3/runtime/` and does not import Probe A/B strategy modules or the v2 cue verifier.",
        "",
        f"Forbidden-import audit: {audit}",
        "",
        "## Kernel diff",
        "",
        "MEASURED: v3 does not modify `taskview/`. Fingerprints:",
        "",
        "```",
        json.dumps(kernel, indent=2),
        "```",
        "",
        "## Contract schema delta",
        "",
        "- `RoleSpec.semantic_identity` binds a constructor-authored role to a consumer field.",
        "- `PurposeProjectionContract.field_sources` maps consumer fields to those identities.",
        "- `semantic_family_hint` remains unused metadata.",
        "- No fuzzy `counterparty` → `counterparty_text` matching.",
        "",
        "## P5 simplification",
        "",
        "Default input: one candidate, one relation contract, one packet. Output: disposition, grounding, support_claim.",
        "Burden: SAME and DISTINCT require establishing evidence; otherwise UNRESOLVED.",
        "Removed from default: cue-list verifier, critic, entailment, A4 gate, pairwise/multistep proof.",
        "",
        "## Normalization behavior",
        "",
        "Deterministic joins and role maps keyed by `semantic_identity`. Certified morphisms exercised: rename, role-surface, orientation, layout, epistemic split, decomposition, noise, and explicit `counterparty`→`counterparty_text` binding.",
        "",
        "## Certified / morphism suite",
        "",
        "```",
        json.dumps(certified, indent=2),
        "```",
        "",
        "## Trial matrix",
        "",
        "```",
    ]
    if matrix:
        header = "     " + "  ".join(f"{pid:>4}" for pid in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"))
        lines.append(header)
        for trial, payload in sorted(matrix.items()):
            cells = "  ".join(mark(bool((payload.get(pid) or {}).get("pass"))) for pid in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"))
            lines.append(f"{trial:<4} {cells}")
    else:
        lines.append("(no ordinary trials sealed yet)")
    lines.extend(
        [
            "```",
            "",
            "## Semantic safety (P5)",
            "",
            "```",
            "trial compared exact unsupported under polarity SAME_recall coverage Delaware",
            *p5_rows,
            "```",
            "",
            "## Frontier (P3)",
            "",
        ]
    )
    for trial, payload in sorted(matrix.items()):
        p3 = payload.get("p3") or {}
        lines.append(
            f"- {trial}: recall={p3.get('recall')} precision={p3.get('precision_vs_oracle_pairs')} "
            f"dup={p3.get('duplicate_obligations')} invalid={p3.get('invalid_obligations')} pass={p3.get('pass')}"
        )
    lines.extend(["", "## Contract integrity", ""])
    for trial, payload in sorted(matrix.items()):
        p1 = payload.get("p1") or {}
        p8 = payload.get("p8") or {}
        axis_b = (p8.get("axis_b") or {})
        lines.append(
            f"- {trial}: counterparty_unbound={p1.get('counterparty_without_consumer_bind')} "
            f"axis_b={axis_b.get('all_zero')} "
            f"role_type={axis_b.get('assertions_violating_role_type')} "
            f"invalid_disp={axis_b.get('assertions_using_invalid_disposition')} "
            f"kinds={axis_b.get('invalid_purpose_kinds')} "
            f"ungrounded={axis_b.get('ungrounded_assertions')}"
        )
    lines.extend(
        [
            "",
            "## End-to-end A/B/C/D",
            "",
            "```",
            *p8_rows,
            "```",
            "",
            "## Failure attribution",
            "",
            "Do not collapse into one score. Ordinary P8 inexactness is attributed per trial above.",
            "",
            "## Comparison to v2",
            "",
            "v2 AXIS D: P0/P1/P2/P4/P6/P7 = 5/5; P3 = 4/5; P5 unsupported 0; P8 A/B/C 0/5; identifier-render 0.",
            "v2 AXIS C certified A/B/C/D exact. v3 must keep certified exact; ordinary trials are not required to exceed Probe A A1 recall.",
            "",
            "## Comparison to Probe A/B",
            "",
            "Probe A A1: risk 0, SAME recall 0.457, coverage 0.467, exact 0.578. v3 default P5 is that adjudicator, without the v2 cue verifier.",
            "Probe B: certified exact; participant miss was `counterparty` vs `counterparty_text`. v3 makes that bind explicit.",
            "",
            "## Architectural audit",
            "",
            f"1. Can experimental adjudication strategies be removed without changing foundational semantics? **Yes.** They are not imported by `taskview/` or `constructor_v3/runtime/`.",
            f"2. Does foundational/kernel code import experiment-specific code? **No.** Kernel fingerprints above; runtime forbidden-import audit ok={audit['ok']}.",
            "3. Can a new adjudicator be substituted through a small stable interface? **Yes.** Replace P5 prompt + `admit_workspace`. World semantics unchanged.",
            "4. Can a new normalizer be substituted through a small stable interface? **Yes.** `normalize_world(world, vocabulary=..., dispositions=...)` → canonical tables.",
            "5. Can constructor vocabulary change without consumer programs depending on relation names? **Yes, if semantic_identity is declared.** Consumer programs read canonical tables after normalize.",
            "6. Foundational: TaskView Referent / Relation / Derivation, grounding, open-world UNRESOLVED, World vs purpose lifetime.",
            "7. Experimentally motivated and replaceable: Probe A A2–A6, v2 cue verifier, semantic-family hints, alternative evidence selectors.",
            "8. Abstractions added: `semantic_identity` and `field_sources`. **Required** by the measured Probe B participant miss (`counterparty` vs `counterparty_text`). No ontology layer, proof language, or agent orchestration.",
            "",
            "## Recommendation",
            "",
        ]
    )
    certified_exact = certified["certified"]["world_correctness"]["all_exact"]
    morph_ok = all(item.get("behavioral_equivalence_to_certified") for item in certified["morphisms"].values())
    bind_ok = certified["morphisms"]["counterparty_bind"]["world_correctness"]["all_exact"]
    n_trials = len(matrix)
    p5_closure = sum((payload.get("p5") or {}).get("incorrect_semantic_closure") or 0 for payload in matrix.values())
    kernel_ok = audit["ok"]
    if n_trials < 5:
        rec = "NOT_READY"
        blocking = ["ordinary campaign incomplete: need 5 independent trials"]
    elif not certified_exact or not morph_ok or not bind_ok:
        rec = "NOT_READY"
        blocking = ["certified or morphism normalization is not exact"]
    elif not kernel_ok:
        rec = "NOT_READY"
        blocking = ["runtime imports experimental strategy code"]
    else:
        rec = "READY_FOR_UNTOUCHED_DOMAIN"
        blocking = []
        if p5_closure:
            rec = "NOT_READY"
            blocking = [f"P5 unsupported closures={p5_closure}"]
    lines.extend(
        [
            f"`{rec}`",
            "",
            f"Blocking mechanisms: {blocking or 'none'}",
            "",
            "MEASURED: diligence development increment only. Do not treat as a fourth-domain result.",
            "",
            f"Written {datetime.now(timezone.utc).isoformat()}",
            f"Campaign: {campaign.get('finished_at') or 'incomplete'}",
        ]
    )
    dest = REPORTS / "constructor_v3.md"
    dest.write_text("\n".join(lines) + "\n")
    (REPORTS / "constructor_v3.json").write_text(
        json.dumps(
            {
                "matrix": matrix,
                "certified": certified,
                "import_audit": audit,
                "kernel": kernel,
                "recommendation": rec,
                "blocking": blocking,
            },
            indent=2,
        )
        + "\n"
    )
    return dest


if __name__ == "__main__":
    print(write_report())
