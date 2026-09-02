"""Frozen Constructor v2 repair report. No further repair iteration."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.constructor_v2.axis_a import ROOT as V2_ROOT
from research.semantic_integration.domains.diligence.constructor_v2.score import score_all
from research.semantic_integration.domains.diligence.evaluator import load_json

REPORTS = V2_ROOT / "reports"
V1 = Path(__file__).resolve().parent.parent / "pass_localization" / "reports" / "pass_localization.json"


def _mark(ok: bool | None) -> str:
    if ok is True:
        return "✓"
    if ok is False:
        return "✗"
    return "·"


def _load(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def v1_p5_summary(v1: dict) -> dict:
    ordinary = v1.get("ordinary_scores") or {}
    closures = 0
    exact_trials = 0
    compared = 0
    correct = 0
    a_exact = b_exact = c_exact = 0
    for i in range(1, 6):
        trial = ordinary.get(f"T{i}") or {}
        p5 = trial.get("p5") or {}
        closures += int(p5.get("incorrect_semantic_closure") or 0)
        compared += int(p5.get("compared") or 0)
        correct += int(p5.get("correct") or 0)
        if p5.get("accuracy") == 1.0:
            exact_trials += 1
        p8 = trial.get("p8") or {}
        if (p8.get("A") or {}).get("pass"):
            a_exact += 1
        if (p8.get("B") or {}).get("exact") or (
            (p8.get("B") or {}).get("pass") and not (p8.get("B") or {}).get("extra")
        ):
            b_exact += 1
        if (p8.get("C") or {}).get("pass"):
            c_exact += 1
    d = (v1.get("d_world_only") or {}).get("score") or {}
    return {
        "p5_unsupported_closure": closures,
        "p5_exact_disposition": (correct / compared) if compared else None,
        "p5_exact_trials": exact_trials,
        "A_exact": a_exact,
        "B_exact": b_exact,
        "C_exact": c_exact,
        "D_WORLD_ONLY_exact": bool(d.get("pass")),
        "invalid_clause_kind_output": "observed in P8 C (auto_renewal_term / extra rolling_term)",
        "identifier_render_failures": 3 if not d.get("pass") else 0,
        "candidate_id_loss": "not quantified in v1; D prefixes were World-qualified handles",
        "REJECT_to_UNRESOLVED": "not isolated in v1",
        "UNRESOLVED_candidate_loss": "not isolated in v1",
        "BASE_grounding": "100%",
        "kernel_changes": False,
    }


def write_report() -> dict:
    axis_a = _load(V2_ROOT / "axis_a" / "results.json")
    axis_b = _load(V2_ROOT / "axis_b" / "results.json")
    axis_c = _load(V2_ROOT / "axis_c" / "results.json")
    axis_d_scores = score_all()
    v1 = _load(V1)
    v1s = v1_p5_summary(v1)
    agg = axis_a.get("aggregate") or {}
    c_scores = axis_c.get("scores") or {}
    d_matrix_lines = ["                     " + "  ".join(f"T{i}" for i in range(1, 6))]
    for pass_id in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7"):
        cells = []
        for i in range(1, 6):
            trial = axis_d_scores.get(f"T{i}", {})
            cells.append(_mark((trial.get(pass_id) or {}).get("pass")))
        d_matrix_lines.append(f"{pass_id:22}" + "  ".join(cells))
    abc_cells = []
    for i in range(1, 6):
        p8 = axis_d_scores.get(f"T{i}", {}).get("p8") or {}
        abc_cells.append(
            f"{_mark((p8.get('A') or {}).get('pass'))}"
            f"{_mark((p8.get('B') or {}).get('exact') if 'exact' in (p8.get('B') or {}) else (p8.get('B') or {}).get('pass'))}"
            f"{_mark((p8.get('C') or {}).get('pass'))}"
        )
    d_matrix_lines.append("P8 A/B/C              " + "  ".join(abc_cells))

    p5_rates = []
    p5_closures = 0
    grounding_fail = 0
    leaks = 0
    stable = {k: 0 for k in ("p0", "p1", "p2", "p3", "p4", "p6", "p7")}
    for i in range(1, 6):
        trial = axis_d_scores.get(f"T{i}", {})
        p5 = trial.get("p5") or {}
        p5_rates.append(p5.get("accuracy"))
        p5_closures += int(p5.get("incorrect_semantic_closure") or 0)
        p2 = trial.get("p2") or {}
        if (p2.get("grounding") or {}).get("ungrounded"):
            grounding_fail += 1
        for key in stable:
            if (trial.get(key) or {}).get("pass"):
                stable[key] += 1
        agent_p0 = V2_ROOT / "axis_d" / "trials" / f"T{i}" / "passes" / "p0" / "agent.json"
        if agent_p0.exists():
            rec = json.loads(agent_p0.read_text())
            leaks += len(rec.get("isolation_leaks") or [])

    p8_a = sum(1 for i in range(1, 6) if ((axis_d_scores.get(f"T{i}") or {}).get("p8") or {}).get("A", {}).get("pass"))
    p8_b = sum(
        1
        for i in range(1, 6)
        if ((axis_d_scores.get(f"T{i}") or {}).get("p8") or {}).get("B", {}).get("exact")
    )
    p8_c = sum(1 for i in range(1, 6) if ((axis_d_scores.get(f"T{i}") or {}).get("p8") or {}).get("C", {}).get("pass"))

    v2_p5_exact = agg.get("accuracy")
    comparison = {
        "P5_unsupported_closure": {
            "v1": v1s["p5_unsupported_closure"],
            "v2_axis_a": agg.get("unsupported_closure"),
            "v2_axis_d": p5_closures,
        },
        "P5_exact_disposition": {
            "v1": v1s["p5_exact_disposition"],
            "v2_axis_a": v2_p5_exact,
        },
        "A_exact": {"v1": f"{v1s['A_exact']}/5 ordinary P8", "v2_axis_c": (c_scores.get("A") or {}).get("pass"), "v2_axis_d": f"{p8_a}/5"},
        "B_exact": {"v1": f"{v1s['B_exact']}/5 ordinary P8", "v2_axis_c": (c_scores.get("B") or {}).get("exact"), "v2_axis_d": f"{p8_b}/5"},
        "C_exact": {"v1": f"{v1s['C_exact']}/5 ordinary P8", "v2_axis_c": (c_scores.get("C") or {}).get("pass"), "v2_axis_d": f"{p8_c}/5"},
        "D_WORLD_ONLY_exact": {"v1": v1s["D_WORLD_ONLY_exact"], "v2_axis_c": (c_scores.get("D") or {}).get("pass")},
        "invalid_clause_kind_output": {"v1": v1s["invalid_clause_kind_output"], "v2_axis_c": (axis_c.get("invalid_kinds") or {}).get("invalid_purpose_kinds")},
        "identifier_render_failures": {"v1": "D prefixes invoice:/contract:", "v2_axis_c": 0 if (c_scores.get("D") or {}).get("pass") else "present"},
        "candidate_id_loss": {"v1": v1s["candidate_id_loss"], "v2_axis_c": not (axis_c.get("fidelity") or {}).get("candidate_identifiers_preserved")},
        "REJECT_to_UNRESOLVED": {"v1": v1s["REJECT_to_UNRESOLVED"], "v2": "explicit mapping REJECT→DISTINCT on identity rows only"},
        "UNRESOLVED_candidate_loss": {"v1": v1s["UNRESOLVED_candidate_loss"], "v2_axis_c": False},
        "BASE_grounding": {"v1": v1s["BASE_grounding"], "v2_axis_c": (axis_c.get("world_validation") or {}).get("ungrounded_assertions")},
        "kernel_changes": {"v1": False, "v2": False},
    }

    answers = {
        "1_unsupported_closure_reduced": {
            "MEASURED": {
                "v1_ordinary_P5_unsupported_closures": v1s["p5_unsupported_closure"],
                "v2_axis_a_unsupported_closures": agg.get("unsupported_closure"),
                "v2_axis_d_unsupported_closures": p5_closures,
            },
            "OBSERVED": "AXIS A is the frozen-packet microbenchmark; AXIS D is full-constructor P5.",
            "HYPOTHESIS": "Verifier plus identity burden reduces unsupported SAME/DISTINCT when packets preserve unresolved language.",
        },
        "2_p5_exact_disposition": {
            "MEASURED": agg.get("accuracy"),
            "OBSERVED": agg,
            "HYPOTHESIS": "Exactness can fall if the verifier conservatively emits UNRESOLVED.",
        },
        "3_verifier_changed_model_disposition": {
            "MEASURED": agg.get("verifier_changed"),
            "OBSERVED": "Counted per audited identity judgment across AXIS A trials.",
        },
        "4_correct_closures_downgraded": {
            "MEASURED": agg.get("correct_downgraded"),
            "OBSERVED": "See AXIS A audit.json initial vs final vs oracle.",
        },
        "5_relation_contracts_rejected_invalid": {
            "MEASURED": axis_b,
            "OBSERVED": "Certified World validators; participant Worlds may still contain extra clause kinds that projection excludes.",
        },
        "6_certified_world_projection_exact": {
            "MEASURED": axis_c.get("all_exact"),
            "OBSERVED": axis_c.get("fidelity"),
        },
        "7_epistemic_preserved": {
            "MEASURED": (axis_c.get("fidelity") or {}).get("candidate_identifiers_preserved")
            and (axis_c.get("fidelity") or {}).get("disposition_mapping_exact"),
        },
        "8_identifiers_rendered_without_mutating_world": {
            "MEASURED": (c_scores.get("A") or {}).get("pass") and (c_scores.get("D") or {}).get("pass"),
            "OBSERVED": "strip_invoice_prefix / strip_contract_prefix at projection only.",
        },
        "9_stable_passes_regress": {
            "MEASURED": stable,
            "required": {k: "5/5" for k in stable},
        },
        "10_remaining_semantic_intelligence": {
            "OBSERVED": "Identity SAME vs UNRESOLVED from bounded prose when establishing cues are weak; DISTINCT pairs not generated by P3 remain missing from B.",
            "HYPOTHESIS": "Burden-of-proof adjudication still requires model intelligence; contracts cannot decide identity from names.",
        },
        "11_remaining_compiler_engineering": {
            "OBSERVED": "Participant clause-kind over-extraction (auto_renewal_term vs auto_renewal) is mechanical typing, not projection. P8 no longer needs an LLM.",
        },
        "12_ready_for_untouched_fourth_domain": {
            "MEASURED": False,
            "OBSERVED": "This campaign is a diligence repair fixture. Fourth-domain readiness requires an untouched domain, not this score.",
            "HYPOTHESIS": "Do not treat diligence v2 scores as domain-general reliability.",
        },
    }

    payload = {
        "experiment_id": "diligence-constructor-v2-repair",
        "model": "composer-2.5",
        "kernel_changes": False,
        "semantic_family_behavior": False,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "axis_a": axis_a,
        "axis_b": axis_b,
        "axis_c": axis_c,
        "axis_d_matrix": axis_d_scores,
        "stable_pass_counts": stable,
        "comparison": comparison,
        "answers": answers,
        "scientific_status": {
            "may_establish": [
                "repair effectiveness on diligence",
                "mechanism-level improvement",
                "non-regression of stable passes",
            ],
            "may_not_establish": [
                "new domain generality",
                "arbitrary-domain reliability",
            ],
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "constructor_v2_repair.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")

    md = f"""# Constructor v2 repair report

Experiment `diligence-constructor-v2-repair`. Model: `composer-2.5`. Kernel unchanged. semantic_family_hint has no v2 behavior.

This is a **diligence repair fixture**, not a new generalization experiment. One frozen v2 implementation was evaluated. Failures were recorded, not iterated.

## AXIS A — semantic adjudication reliability

10 isolated P5 trials on frozen identity packets. Fresh workspaces. Packets only.

```
unsupported closures: {agg.get("unsupported_closure")}
exact disposition: {agg.get("exact")} / {agg.get("compared")} = {agg.get("accuracy")}
under-closure: {agg.get("under_closure")}
polarity SAME↔DISTINCT: {agg.get("polarity")}
verifier changed: {agg.get("verifier_changed")}
correct closures downgraded: {agg.get("correct_downgraded")}
confusion: {json.dumps(agg.get("confusion"))}
```

Primary target: 0 unsupported closures.

## AXIS B — relation-contract integrity

Certified World + projected C:

```
role type: {axis_b.get("assertions_violating_role_type")}
invalid disposition: {axis_b.get("assertions_using_invalid_disposition")}
invalid purpose kinds: {axis_b.get("invalid_purpose_clause_value_kinds")}
algebra: {axis_b.get("algebra_consistency_violations")}
ungrounded: {axis_b.get("ungrounded_assertions")}
all zero: {axis_b.get("all_zero")}
rejected: {json.dumps(axis_b.get("rejected"))}
```

## AXIS C — certified-World projection (no sources)

```
A exact: {(c_scores.get("A") or {}).get("pass")}
B exact: {(c_scores.get("B") or {}).get("exact")}
C exact: {(c_scores.get("C") or {}).get("pass")}
D_WORLD_ONLY exact: {(c_scores.get("D") or {}).get("pass")}
all exact: {axis_c.get("all_exact")}
source reads: {axis_c.get("source_reads")}
identifier preservation: {(axis_c.get("fidelity") or {}).get("candidate_identifiers_preserved")}
```

## AXIS D — constructor non-regression

```
{chr(10).join(d_matrix_lines)}
```

Required: P0–P4, P6, P7 = 5/5; BASE grounding 100%; repository/isolation leaks 0.

P5/P8 reported separately and not collapsed into one success number.

## Comparison to v1

```
                         v1                              v2
P5 unsupported closure    {v1s["p5_unsupported_closure"]} ordinary trial-closures     AXIS A {agg.get("unsupported_closure")}; AXIS D {p5_closures}
P5 exact disposition      {v1s["p5_exact_disposition"]}                         AXIS A {v2_p5_exact}
A exact                   {v1s["A_exact"]}/5 P8                    AXIS C {(c_scores.get("A") or {}).get("pass")}; AXIS D {p8_a}/5
B exact                   {v1s["B_exact"]}/5 P8                    AXIS C {(c_scores.get("B") or {}).get("exact")}; AXIS D {p8_b}/5
C exact                   {v1s["C_exact"]}/5 P8                    AXIS C {(c_scores.get("C") or {}).get("pass")}; AXIS D {p8_c}/5
D_WORLD_ONLY exact         {v1s["D_WORLD_ONLY_exact"]}                         AXIS C {(c_scores.get("D") or {}).get("pass")}
invalid clause/kind      v1 P8 extras                     AXIS C projected kinds { (axis_c.get("invalid_kinds") or {}).get("invalid_purpose_kinds") }
identifier-render         D prefixes                        AXIS C D {(c_scores.get("D") or {}).get("pass")}
candidate-id loss         v1 not isolated                    AXIS C preserved {(axis_c.get("fidelity") or {}).get("candidate_identifiers_preserved")}
REJECT→UNRESOLVED         v1 not isolated                    mapping explicit; identity REJECT→DISTINCT
UNRESOLVED candidate loss v1 not isolated                  AXIS C false
BASE grounding            100%                            certified ungrounded {(axis_c.get("world_validation") or {}).get("ungrounded_assertions")}
kernel changes            no                              no
```

n_v1 ordinary = 5 trials; n_AXIS A = 10 packet trials. Do not overclaim statistical generality.

## Answers

1. **Did proof-carrying semantic adjudication reduce unsupported closure?** MEASURED: v1 ordinary P5 unsupported closures = {v1s["p5_unsupported_closure"]}; v2 AXIS A = {agg.get("unsupported_closure")}; v2 AXIS D = {p5_closures}. OBSERVED: see AXIS A audits (`initial_disposition`, `verifier_result`, `final_disposition`). HYPOTHESIS: the verifier blocks unresolved-preservation closures without resampling.

2. **P5 exact disposition accuracy?** MEASURED AXIS A: {v2_p5_exact}.

3. **How often did the verifier change a model disposition?** MEASURED AXIS A: {agg.get("verifier_changed")}.

4. **Were any correct closures incorrectly downgraded?** MEASURED AXIS A: {agg.get("correct_downgraded")}.

5. **Did relation contracts reject invalid World/purpose semantics?** MEASURED AXIS B all_zero={axis_b.get("all_zero")}. Rejected assertions are listed, not dropped.

6. **Did certified-World projection produce exact A/B/C/D?** MEASURED: {axis_c.get("all_exact")}.

7. **Were epistemic states preserved through projection?** MEASURED: candidate IDs preserved {(axis_c.get("fidelity") or {}).get("candidate_identifiers_preserved")}; B exact {(c_scores.get("B") or {}).get("exact")}.

8. **Were identifiers rendered correctly without mutating World identity?** MEASURED AXIS C A/D exact; rendering is projection-only prefix strip.

9. **Did previously stable constructor passes regress?** MEASURED: {stable}. Required 5/5 each.

10. **Remaining failure still requiring semantic intelligence?** OBSERVED: identity burden when evidence is prose without establishing language; missing DISTINCT frontier pairs.

11. **Remaining failure that is compiler/runtime engineering?** OBSERVED: participant over-extracted clause kinds; schema-flexible World compilation still varies across trials.

12. **Ready for an untouched fourth-domain test?** MEASURED: no. This experiment does not establish new-domain generality.

## Scientific status

May establish: repair effectiveness on diligence; mechanism-level improvement; non-regression of stable passes.

May NOT establish: new domain generality; arbitrary-domain reliability.

## Stop

No fourth domain. No RAW-vs-WORLD. No kernel changes. No semantic-family behavior. No further repair iteration in this campaign.
"""
    (REPORTS / "constructor_v2_repair.md").write_text(md)
    published = V2_ROOT.parent / "reports"
    published.mkdir(parents=True, exist_ok=True)
    (published / "constructor_v2_repair.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    (published / "constructor_v2_repair.md").write_text(md)
    return payload


if __name__ == "__main__":
    print(json.dumps(write_report(), indent=2, sort_keys=True)[:4000])
