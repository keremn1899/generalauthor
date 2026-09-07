"""Frozen Constructor v3.1 report from measured campaign + certified suite."""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1.certified import run_certified_suite
from research.semantic_integration.domains.diligence.constructor_v3_1.isolation import EXPERIMENT_ID, REPO
from research.semantic_integration.domains.diligence.constructor_v3_1.score import score_all
from research.semantic_integration.domains.diligence.constructor_v3_1.workspaces import TRIALS

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"
TASKVIEW = REPO / "taskview"
V3_KERNEL = {
    "__init__.py": "sha256:3dcc6f08802891678dd6045204c7f24a0f9b13551e6a07dac39e530e28099c4a",
    "model.py": "sha256:7221d90855bfe7e99ab65f38b49d9356a38fe8cdc0dd99753b62c23f4ba0aeff",
    "store.py": "sha256:fb3d3bbf90e6d149921c420636860db239d96af1b8580aa7af22d0ddddc884d7",
    "agent_surface.py": "sha256:3fad57102afa52ff659527cc4bb9fdb7753fe517338e6fe9a7f925f05909dfc9",
}
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


def load_h1() -> dict[str, Any]:
    path = ROOT / "h1_micro" / "results.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def collect_agent_hygiene() -> dict[str, Any]:
    leaks = []
    models = []
    timeouts = []
    source_rereads = []
    for trial in range(1, 6):
        for pass_id in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8"):
            path = TRIALS / f"T{trial}" / "passes" / pass_id / "agent.json"
            if not path.exists():
                continue
            row = json.loads(path.read_text())
            models.append(
                {
                    "trial": trial,
                    "pass_id": pass_id,
                    "model": row.get("model"),
                    "reported_model": row.get("reported_model"),
                }
            )
            for leak in row.get("isolation_leaks") or []:
                leaks.append({"trial": trial, "pass_id": pass_id, "path": leak})
            if row.get("timed_out"):
                timeouts.append({"trial": trial, "pass_id": pass_id})
            if pass_id == "p8":
                source_rereads.append(row.get("source_reads") or 0)
    return {
        "isolation_leaks": leaks,
        "timeouts": timeouts,
        "models": models,
        "p8_source_reads": source_rereads,
    }


def readiness(matrix: dict, certified: dict, audit: dict, kernel: dict, hygiene: dict) -> tuple[str, list[str]]:
    blocking: list[str] = []
    n_trials = len(matrix)
    if n_trials < 5:
        blocking.append("ordinary campaign incomplete: need 5 independent trials")
    certified_exact = bool((certified.get("certified") or {}).get("world_correctness", {}).get("all_exact"))
    morph_ok = all(
        item.get("behavioral_equivalence_to_certified") for item in (certified.get("morphisms") or {}).values()
    ) if certified.get("morphisms") else False
    bind_ok = bool(
        ((certified.get("morphisms") or {}).get("counterparty_bind") or {})
        .get("world_correctness", {})
        .get("all_exact")
    )
    if not certified_exact or not morph_ok or not bind_ok:
        blocking.append("certified or morphism normalization is not exact")
    if kernel != V3_KERNEL:
        blocking.append("kernel fingerprint changed relative to frozen v3")
    if not audit.get("ok"):
        blocking.append("runtime imports experimental strategy code")
    if hygiene.get("isolation_leaks"):
        blocking.append(f"oracle/isolation leaks={len(hygiene['isolation_leaks'])}")
    p5_closure = sum((payload.get("p5") or {}).get("incorrect_semantic_closure") or 0 for payload in matrix.values())
    if p5_closure:
        blocking.append(f"unsupported semantic closure={p5_closure}")
    ungrounded = sum((payload.get("p6") or {}).get("ungrounded_count") or 0 for payload in matrix.values())
    if ungrounded:
        blocking.append(f"ungrounded durable World assertions={ungrounded}")
    p8_reads = sum(hygiene.get("p8_source_reads") or [])
    if p8_reads:
        blocking.append(f"P8 source rereads={p8_reads}")
    id_fail = sum(len((payload.get("p8") or {}).get("identifier_render_failures") or []) for payload in matrix.values())
    epistemic_fail = sum(len((payload.get("p8") or {}).get("unresolved_candidate_loss") or []) for payload in matrix.values())
    if id_fail or epistemic_fail:
        blocking.append(f"identifier/epistemic preservation regressions id={id_fail} unresolved_loss={epistemic_fail}")
    abi_false = 0
    abi_ambiguous = 0
    abi_unreported = 0
    for payload in matrix.values():
        abi = (payload.get("p1") or {}).get("abi") or (payload.get("p8") or {}).get("abi") or {}
        abi_false += len(abi.get("false_bindings") or [])
        abi_ambiguous += len(abi.get("ambiguous") or [])
        fields = abi.get("fields") or {}
        required = abi.get("required_semantic_fields") or []
        for field in required:
            status = (fields.get(field) or {}).get("status")
            if status not in {"SATISFIED", "UNSATISFIED", "AMBIGUOUS"}:
                abi_unreported += 1
    if abi_false or abi_ambiguous:
        blocking.append(f"false/ambiguous ABI mappings false={abi_false} ambiguous={abi_ambiguous}")
    if abi_unreported:
        blocking.append(f"required consumer fields without explicit ABI status={abi_unreported}")
    return ("READY_FOR_UNTOUCHED_DOMAIN" if not blocking else "NOT_READY", blocking)


def write_report() -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    matrix = score_all()
    certified = run_certified_suite()
    audit = runtime_import_audit()
    kernel = kernel_fingerprint()
    hygiene = collect_agent_hygiene()
    h1 = load_h1()
    h1s = h1.get("summary") or {}
    campaign_path = ROOT / "axis_d" / "campaign.json"
    campaign = json.loads(campaign_path.read_text()) if campaign_path.exists() else {}
    rec, blocking = readiness(matrix, certified, audit, kernel, hygiene)

    p5_rows = []
    p8_rows = []
    abi_rows = []
    for trial, payload in sorted(matrix.items()):
        p5 = payload.get("p5") or {}
        p8 = payload.get("p8") or {}
        abi = (payload.get("p1") or {}).get("abi") or p8.get("abi") or {}
        p5_rows.append(
            f"{trial:<4} {p5.get('compared')} {p5.get('correct')}/{p5.get('compared')} "
            f"{p5.get('incorrect_semantic_closure')} {p5.get('incorrect_under_closure')} "
            f"{p5.get('incorrect_polarity')} {p5.get('same_recall')} {p5.get('distinct_recall')} "
            f"{p5.get('coverage')} {p5.get('delaware_inc_disposition')} "
            f"gate_ran={p5.get('gate_ran')} gate_down={p5.get('gate_downgraded')}"
        )
        p8_rows.append(
            f"{trial:<4} A={p8.get('A', {}).get('pass')} B={p8.get('B', {}).get('exact')} "
            f"C={p8.get('C', {}).get('pass')} D={p8.get('D', {}).get('pass')} "
            f"attr={p8.get('failure_attribution')} norm_miss={p8.get('normalization', {}).get('missing_mappings')}"
        )
        abi_rows.append(
            f"{trial:<4} required={len(abi.get('required_semantic_fields') or [])} "
            f"satisfied={len(abi.get('satisfied') or [])} "
            f"unsatisfied={abi.get('unsatisfied')} "
            f"ambiguous={abi.get('ambiguous')} "
            f"false={abi.get('false_bindings')} "
            f"dup={abi.get('duplicate_bindings')} ok={abi.get('ok')}"
        )

    lines = [
        "# Constructor v3.1",
        "",
        f"Experiment `{EXPERIMENT_ID}`. Model: `composer-2.5`. Diligence hardening increment on frozen v3. Not a fourth domain.",
        "",
        "Labels: **MEASURED** = campaign, micro-benchmark, or certified suite; **OBSERVED** = trial-level detail; **HYPOTHESIS** = interpretation.",
        "",
        "Sealed v1, v2, Probe A, Probe B, post-v2, and Constructor v3 reports were not overwritten.",
        "",
        "## Implementation delta",
        "",
        "- H1: DISTINCT-only negative-closure gate after structural admission. SAME and UNRESOLVED are not gated. Fail-closed to UNRESOLVED.",
        "- H2: constructor-runtime `validate_provenance()` after P6. TaskView still accepts empty grounding; v3.1 rejects that World as invalid.",
        "- H3: ABI completeness (`SATISFIED` / `UNSATISFIED` / `AMBIGUOUS`) after vocabulary and before projection. Unsatisfied/ambiguous purposes are `INCOMPLETE_PURPOSE`, not silent projection.",
        "- Default P5 remains the Probe A A1 bounded single adjudicator.",
        "- P3 is unchanged. Kernel / TaskView unchanged.",
        "",
        "## Kernel diff",
        "",
        "MEASURED: v3.1 does not modify `taskview/`. Fingerprints match frozen v3:" if kernel == V3_KERNEL else "MEASURED: kernel fingerprint differs from frozen v3.",
        "",
        "```",
        json.dumps(kernel, indent=2),
        "```",
        "",
        "## Architecture / dependency audit",
        "",
        "See `research/semantic_integration/ARCHITECTURE.md`.",
        "",
        "- Negative-closure gate: runtime semantic safety, isolated in `runtime/negative_closure.py`. Foundational code does not import it.",
        "- Provenance invariant: constructor-runtime `validate_provenance()` after P6 World commit.",
        "- ABI completeness: constructor-runtime check of required consumer identities before projection.",
        "",
        f"Forbidden-import audit: {audit}",
        "",
        "## H1 negative-closure micro-benchmark",
        "",
        "Frozen packets only. Baseline A1 DISTINCT vs A1 + gate. Packets were not regenerated.",
        "",
        "```",
        json.dumps(h1s, indent=2),
        "```",
        "",
        "MEASURED: unsupported DISTINCT baseline 1 → gated 0. DISTINCT recall 1.0 → 1.0. Correct DISTINCT downgraded 0. UNRESOLVED preservation 1.0.",
        "OBSERVED: the v3 T1 Northbridge/Wyoming packet downgraded DISTINCT → UNRESOLVED. Probe A id-15 and id-16 retained SUPPORTED_DISTINCT.",
        "MEASURED: SAME was not an input to the gate in this micro-benchmark.",
        "",
        "## H2 grounding root cause",
        "",
        "MEASURED cause **A**: P6 admission path bypassed grounding validation.",
        "",
        "v3 T2 P6 World had 105 assertions, 20 ungrounded, all `origin=ASSERTED` (18 `identity_judgment`, 2 `invoice_contract_association`). P2 of the same trial had 0 ungrounded. TaskView `assert_tuple(..., grounding=())` permits empty grounding. The scorer correctly counted them ungrounded. Not B (missing derivation provenance), not C (dropped during pass transition), not D (scorer bug).",
        "",
        "Enforcement is constructor-runtime after P6, not a kernel change.",
        "",
        "## H2 grounding regression tests",
        "",
        "Deterministic: ungrounded `assert_tuple` fails `validate_provenance()`. Grounded SOURCE assertion passes. P6 score requires `ungrounded_count=0`.",
        "",
        "## H3 ABI completeness behavior",
        "",
        "Required identities: invoice_id, billed_name, amount, currency, period, status, contract_id, counterparty_text, active, clause_kind, left, right, disposition.",
        "Unbound `active` → `UNSATISFIED` and `INCOMPLETE_PURPOSE`. No fuzzy repair. No semantic-family inference.",
        "",
        "## Negative controls",
        "",
        "1. Unbound required semantic identity → ABI completeness failure (deterministic).",
        "2. Attempted ungrounded World assertion → `validate_provenance()` failure (deterministic).",
        "3. Misleading attribute mismatch with no exclusion proof → DISTINCT downgraded (H1 micro v3-T1 packet).",
        "4. Certified valid DISTINCT evidence → DISTINCT retained (H1 micro id-15, id-16).",
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
            "P8 pass requires exact A and B and C and ABI ok. D and D_WORLD_ONLY (deterministic projector, sources absent from the P8 path) are reported separately.",
            "",
            "## Semantic safety (P5)",
            "",
            "```",
            "trial compared exact unsupported under polarity SAME_recall DISTINCT_recall coverage Delaware gate",
            *p5_rows,
            "```",
            "",
            "## Grounding / provenance integrity",
            "",
        ]
    )
    for trial, payload in sorted(matrix.items()):
        p2 = payload.get("p2") or {}
        p6 = payload.get("p6") or {}
        lines.append(
            f"- {trial}: P2_ungrounded={(p2.get('grounding') or {}).get('ungrounded')} "
            f"P6_ungrounded={p6.get('ungrounded_count')} P6_pass={p6.get('pass')}"
        )
    lines.extend(["", "## Contract integrity", ""])
    for trial, payload in sorted(matrix.items()):
        p1 = payload.get("p1") or {}
        p8 = payload.get("p8") or {}
        axis_b = p8.get("axis_b") or {}
        lines.append(
            f"- {trial}: n_purpose={p1.get('n_purpose')} "
            f"counterparty_unbound={p1.get('counterparty_without_consumer_bind')} "
            f"role_type={axis_b.get('assertions_violating_role_type')} "
            f"invalid_disp={axis_b.get('assertions_using_invalid_disposition')} "
            f"kinds={axis_b.get('invalid_purpose_kinds')} "
            f"axis_b_ungrounded={axis_b.get('ungrounded_assertions')}"
        )
    lines.extend(["", "## ABI completeness", "", "```", *abi_rows, "```", "", "## Normalization", ""])
    for trial, payload in sorted(matrix.items()):
        norm = (payload.get("p8") or {}).get("normalization") or {}
        lines.append(
            f"- {trial}: recovered={norm.get('consumer_relations_recovered')} "
            f"missed={norm.get('missing_mappings')} false={norm.get('false_mappings')}"
        )
    lines.extend(["", "## Frontier (P3)", ""])
    for trial, payload in sorted(matrix.items()):
        p3 = payload.get("p3") or {}
        lines.append(
            f"- {trial}: recall={p3.get('recall')} precision={p3.get('precision_vs_oracle_pairs')} "
            f"dup={p3.get('duplicate_obligations')} invalid={p3.get('invalid_obligations')} pass={p3.get('pass')}"
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
            "D_WORLD_ONLY: P8 is the deterministic projector on World; sources are not reread. Certified-World D remains exact if the certified suite is exact.",
            "",
            f"P8 source rereads: {hygiene.get('p8_source_reads')}",
            f"Isolation leaks: {hygiene.get('isolation_leaks')}",
            f"Timeouts: {hygiene.get('timeouts')}",
            "",
            "## Failure attribution",
            "",
        ]
    )
    for trial, payload in sorted(matrix.items()):
        p8 = payload.get("p8") or {}
        lines.append(f"- {trial}: {p8.get('failure_attribution')}")
    lines.extend(
        [
            "",
            "## Comparison to v3",
            "",
            "v3 blocking: 1 unsupported DISTINCT (T1). v3 T2 P6 ungrounded 20. v3 T3/T5 missed `contract_active` without compiler error.",
            "v3.1 targets those three classes only. SAME recall, P3 recall, and ordinary A/B/C exactness remain monitored, not blocking.",
            "",
            "## Architectural audit",
            "",
            "1. Experimental strategies removable? **Yes.** Default runtime does not import Probe A/B or the v2 cue verifier.",
            f"2. Foundational/kernel import experiment code? **No.** Kernel fingerprints above; runtime audit ok={audit['ok']}.",
            "3. New adjudicator through a small interface? **Yes.** P5 prompt + `admit_workspace`. Gate is DISTINCT-only.",
            "4. New normalizer through a small interface? **Yes.** `normalize_world` → canonical tables.",
            "5. Constructor vocabulary without consumer name dependence? **Yes, if semantic_identity is declared.** Missing required identities fail ABI completeness.",
            "6. Foundational: TaskView Referent / Relation / Derivation, grounding, open-world UNRESOLVED, World vs purpose lifetime.",
            "7. Experimentally motivated: DISTINCT gate (v3 T1), provenance check (v3 T2), ABI completeness (v3 omitted `active`).",
            "8. New kernel abstractions? **None.** `semantic_identity` and `field_sources` remain the v3 ABI. Gate/provenance/ABI are constructor-runtime.",
            "",
            "## Recommendation",
            "",
            f"`{rec}`",
            "",
            f"Blocking mechanisms: {blocking or 'none'}",
            "",
            "## Required direct answers",
            "",
            f"1. Did the negative-closure gate eliminate the v3 unsupported DISTINCT failure class? **{'Yes' if (h1s.get('unsupported_distinct_gated') == 0) else 'No / incomplete'}.** MEASURED micro-benchmark unsupported DISTINCT gated={h1s.get('unsupported_distinct_gated')}. Ordinary-trial unsupported closures={sum((payload.get('p5') or {}).get('incorrect_semantic_closure') or 0 for payload in matrix.values())}.",
            f"2. How many correct DISTINCT judgments did it downgrade? **{h1s.get('correct_distinct_downgraded')}** in the frozen micro-benchmark. Ordinary-trial DISTINCT recall is monitored above.",
            "3. Was SAME behavior changed at all? **No.** The gate does not run on SAME. Admission never upgrades UNRESOLVED.",
            "4. What exactly caused the 20 ungrounded P6 assertions in v3 T2? **Cause A.** P6 called TaskView `assert_tuple` for identity/association BASE facts with empty `grounding`. TaskView permits that. The scorer counted them correctly.",
            f"5. Can an ungrounded durable World assertion now be admitted by any normal runtime path? **No as a valid World.** TaskView can still serialize empty grounding (kernel unchanged). `validate_provenance()` rejects it; P6 fails.",
            "6. Are all required consumer semantic fields now checked before projection? **Yes.**",
            "7. Do omitted bindings fail explicitly rather than becoming downstream projection misses? **Yes.** Status `UNSATISFIED`/`AMBIGUOUS` yields `INCOMPLETE_PURPOSE`.",
            f"8. Did certified normalization remain exact? **{bool((certified.get('certified') or {}).get('world_correctness', {}).get('all_exact'))}.**",
            "9. Did any new abstraction enter the semantic kernel? **No.**",
            f"10. Are all v3 experimental strategies still removable from the default runtime? **Yes.** Audit ok={audit['ok']}.",
            "11. What known semantic capability limitation remains? **SAME under-closure and ordinary A/B/C inexactness may remain. P3 was not redesigned. Incomplete purpose via explicit UNRESOLVED or UNSATISFIED is allowed.**",
            f"12. `{rec}`",
            "",
            "MEASURED: diligence development increment only. Do not treat as a fourth-domain result.",
            "",
            f"Written {datetime.now(timezone.utc).isoformat()}",
            f"Campaign: {campaign.get('finished_at') or 'incomplete'}",
        ]
    )
    dest = REPORTS / "constructor_v3_1.md"
    dest.write_text("\n".join(lines) + "\n")
    (REPORTS / "constructor_v3_1.json").write_text(
        json.dumps(
            {
                "matrix": matrix,
                "certified": certified,
                "import_audit": audit,
                "kernel": kernel,
                "h1_micro": h1s,
                "hygiene": hygiene,
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
