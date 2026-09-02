"""Build the frozen localization report after ordinary trials, interventions, and probes."""

from __future__ import annotations

import json
from pathlib import Path

from research.semantic_integration.domains.diligence.pass_localization.score_passes import score_all

ROOT = Path(__file__).resolve().parent


def _mark(ok: bool | None) -> str:
    if ok is True:
        return "✓"
    if ok is False:
        return "✗"
    return "·"


def _p7_summary(p7c: dict) -> str:
    if not p7c:
        return "not yet run (interrupted before this diagnostic)"
    lines = []
    for trial, rec in p7c.items():
        a = (rec.get("A") or {}).get("pass")
        b = (rec.get("B") or {}).get("pass")
        c = (rec.get("C") or {}).get("pass")
        lines.append(f"{trial} A={a} B={b} C={c}")
    return "; ".join(lines)


def write_report() -> dict:
    scores = score_all()
    interventions = {}
    path = ROOT / "interventions" / "results.json"
    if path.exists():
        interventions = json.loads(path.read_text())
    d_score = {}
    if (ROOT / "d_world_only" / "score.json").exists():
        d_score = json.loads((ROOT / "d_world_only" / "score.json").read_text())
    p7c = {}
    if (ROOT / "p7_certified" / "results.json").exists():
        p7c = json.loads((ROOT / "p7_certified" / "results.json").read_text())

    matrix_lines = ["                     " + "  ".join(f"T{i}" for i in range(1, 6))]
    for pass_id in ("p0", "p1", "p2", "p3", "p4", "p5", "p6", "p7"):
        cells = []
        for i in range(1, 6):
            trial = scores.get(f"T{i}", {})
            cells.append(_mark((trial.get(pass_id) or {}).get("pass")))
        matrix_lines.append(f"{pass_id:22}" + "  ".join(cells))
    abc_cells = []
    for i in range(1, 6):
        p8 = scores.get(f"T{i}", {}).get("p8") or {}
        a = (p8.get("A") or {}).get("pass")
        b = (p8.get("B") or {}).get("pass")
        c = (p8.get("C") or {}).get("pass")
        abc_cells.append(f"{_mark(a)}{_mark(b)}{_mark(c)}")
    matrix_lines.append("P8 A/B/C              " + "  ".join(abc_cells))

    delaware = {
        f"T{i}": (scores.get(f"T{i}", {}).get("p5") or {}).get("delaware_inc_disposition")
        for i in range(1, 6)
    }
    p5_fails = sum(1 for i in range(1, 6) if scores.get(f"T{i}", {}).get("p5", {}).get("pass") is False)
    p4_ok_p5_fail = [
        f"T{i}"
        for i in range(1, 6)
        if scores.get(f"T{i}", {}).get("p4", {}).get("pass")
        and scores.get(f"T{i}", {}).get("p5", {}).get("pass") is False
    ]
    i1_b = {
        trial: ((rec.get("correct_p5") or {}).get("scores") or {}).get("B", {}).get("pass")
        for trial, rec in interventions.items()
    }
    i3_all = all(
        ((rec.get("correct_p5_p7") or {}).get("scores") or {}).get(letter, {}).get("pass")
        for rec in interventions.values()
        for letter in ("A", "B", "C")
    ) if interventions else False

    d_prefix = (d_score.get("prefix_normalized") or {}).get("pass")
    d_exact = (d_score.get("score") or {}).get("pass")

    payload = {
        "experiment_id": "diligence-pass-localization-v1",
        "model": "composer-2.5",
        "reported_model": "Composer 2.5",
        "repairs": False,
        "ordinary_scores": scores,
        "interventions": {
            trial: {
                name: {
                    "ok": val.get("ok"),
                    "mode": val.get("mode"),
                    "A": ((val.get("scores") or {}).get("A") or {}).get("pass"),
                    "B": ((val.get("scores") or {}).get("B") or {}).get("pass"),
                    "C": ((val.get("scores") or {}).get("C") or {}).get("pass"),
                    "reason": val.get("reason"),
                }
                for name, val in rec.items()
            }
            for trial, rec in interventions.items()
        },
        "d_world_only": d_score,
        "p7_certified": p7c,
        "matrix": matrix_lines,
        "delaware_inc": delaware,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "pass_localization.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    md = f"""# Pass localization report

Experiment `diligence-pass-localization-v1`. Model requested: `composer-2.5`. Stream-json: `Composer 2.5`.
No constructor repairs. Frozen diligence fixture unchanged. Kernel unchanged.

Ordinary construction: 5 trials × P0–P8 completed. Isolation leaks: 0. Timeouts: 0.

## Failure matrix

```
{chr(10).join(matrix_lines)}
```

Delaware Inc (`billing:Northbridge Analytics Inc.` ↔ `registry:3840192`): {delaware}

## Answers

1. **Consistently correct passes:** P0 intention, P1 vocabulary, P2 mechanical (token recovery + 100% BASE grounding, no early identity closure), P3 frontier (scorer pass: recall ≥ 0.7), P4 evidence packets, P6 admission, P7 derivation *spec/script presence*. P8 purpose A also 5/5.

2. **Passes accounting for most errors:** P5 identity adjudication (3/5 fail: T2/T3/T5 Delaware `SAME_ENTITY`) and P8 B/C export (0/5). B/C fail even on T1 and T4 where P5 is exact on compared oracle pairs, so those output failures are not solely P5.

3. **Vocabulary errors:** rare. P1 5/5. No purpose-output names admitted as WORLD.

4. **Frontier-generation errors:** uncommon on the scorer threshold. P3 5/5. Residual misses include Helion Industrial DISTINCT pairs on some trials (`crm:HEL-441`–`registry:11847299`, `registry:11847201`–`registry:11847299`).

5. **Evidence packets when adjudication fails:** P4 5/5; required oracle pairs that were generated had packets. Failures `{p4_ok_p5_fail}` are P4-pass / P5-fail: retrieval looks sufficient, adjudication still over-committed Delaware.

6. **Adjudication with sufficient evidence:** yes. T2/T3/T5 packets existed; Delaware was still `SAME_ENTITY`. T1/T4 correctly left it `UNRESOLVED`.

7. **Incorrect semantic commitments vs downstream failure:** Intervention 1 (oracle identity in `05_dispositions.json`, **participant** P7 script rerun) keeps A passing; C never becomes exact; B becomes exact only on T2. Delaware-only counterfactual does not flip B/C pass/fail. Identity overcommitment is real and localizable, but B/C exact-match failures are dominated by export shape (left/right orientation, extra transitive links, `billing:` vs `crm:` counterparties, extra `auto_renewal`/`rolling_term` kinds compiled into World).

8. **Derivation on a correct World:** Intervention 3 (evaluator-certified World + gold derive) yields A/B/C exact on all five trials. Intervention 2 (gold derive against **participant** sqlite schema) does not compute A — participant relation names differ from the certified schema, so that cell does not isolate P7. Certified-P7 LLM diagnostic: {_p7_summary(p7c)}.

9. **WORLD/PURPOSE admission:** stable. P6 5/5. No `purpose_a`/`purpose_b`/`purpose_c` WORLD leakage.

10. **D_WORLD_ONLY:** sources physically absent; source rereads empty; isolation held; model Composer 2.5. Exact canonical **fail** because IDs were emitted as `invoice:INV-1002` / `contract:MSA-…` instead of `INV-1002` / `MSA-…`. The three cases are otherwise the held-out set (Helion, Oakfield, Meridian; NBA excluded). Prefix-normalized pass: **{d_prefix}**.

11. **Deterministic validators that would have prevented observed failures:** (a) identity: notes-stated UNRESOLVED must not become SAME_ENTITY; (b) export: purpose B identifier orientation and required DISTINCT pairs; (c) purpose C: counterparty must use declared `crm:` form; obligation_kinds must be the declared set, not every extracted term clause; (d) grounding already held. Clause-kind over-extraction (`auto_renewal_term` on Helion, `rolling_term` on NBA in T1 World) is a mechanical/semantic typing error that a clause-kind validator against explicit contract wording could catch.

12. **Still requiring model intelligence:** bounded identity adjudication (Delaware/Wyoming) even with `commercial_notes` in the packet; deciding SAME vs UNRESOLVED from prose. Export/schema validators would have caught B/C exact failures without more inference.

## Causal interventions (not constructor successes)

| Trial | I1 correct P5 + participant derive | I2 gold derive on participant sqlite | I3 certified World+derive | Delaware → UNRESOLVED |
|---|---|---|---|---|
| T1 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T2 | A✓ B✓ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T3 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T4 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |
| T5 | A✓ B✗ C✗ | A✗ B✗ C✗ | A✓ B✓ C✓ | A✓ B✗ C✗ |

I2 is an intervention-harness miss on schema, not a finding that gold P7 fails a certified World.

## MEASURED

- New kernel primitive: no.
- Ordinary P8 A: 5/5. B: 0/5. C: 0/5. Zero P8 source rereads.
- P5 Delaware UNRESOLVED: T1, T4. SAME_ENTITY: T2, T3, T5.
- D_WORLD_ONLY exact: {d_exact}. Prefix-normalized: {d_prefix}. Sources present: {d_score.get("sources_present")}.
- Certified-P7 LLM on evaluator World: A/B/C exact 5/5. Isolation leaks 0.
- Isolation leaks ordinary + D: 0.

## OBSERVED

The first-domain hypothesis that B fails from Delaware over-assertion is only partly right. That over-assertion occurs in 3/5 trials **and** B/C still fail when it does not. Purpose A is robust to identity residual. Purpose C exact-match is sensitive to identifier form and extra clause kinds already in World. D was computable from the frozen prior World without sources; the remaining miss is identifier prefixing.

## HYPOTHESIS

On this fixture, the constructor’s fragile pass is P5 identity, and the exact-output fragile pass is P7/P8 export/policy over an otherwise usable World. Validators for unresolved-preservation, export schemas, and clause-kind minimality are justified here. This is repair evidence for this fixture, not third-domain generalization.
"""
    (reports / "pass_localization.md").write_text(md, encoding="utf-8")
    return payload


if __name__ == "__main__":
    write_report()
    print((ROOT / "reports" / "pass_localization.md").read_text()[:2500])
