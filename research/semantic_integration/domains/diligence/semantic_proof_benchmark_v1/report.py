"""Freeze Probe A reports from sealed strategy scores. No rerun."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.paths import (
    REPORTS,
    ROOT,
    STRATEGIES,
)
from research.semantic_integration.domains.diligence.semantic_proof_benchmark_v1.prompts import (
    INFERENCE_STRATEGIES,
)

ORDER = ("a0_v2", *INFERENCE_STRATEGIES)


def load_scores() -> dict[str, dict]:
    out = {}
    for name in ORDER:
        path = STRATEGIES / name / "risk_coverage.json"
        if path.exists():
            out[name] = json.loads(path.read_text())
    return out


def table_line(name: str, score: dict) -> str:
    def fmt(value: float | None, digits: int = 3) -> str:
        if value is None:
            return "n/a"
        return f"{value:.{digits}f}"

    return (
        f"{name:<22} {fmt(score.get('semantic_risk')):>8} "
        f"{fmt(score.get('semantic_coverage')):>10} "
        f"{fmt(score.get('SAME_recall')):>12} "
        f"{fmt(score.get('exact_accuracy')):>8}"
    )


def write_reports() -> dict:
    scores = load_scores()
    all_rows = []
    for name in ORDER:
        path = STRATEGIES / name / "judgments.json"
        if path.exists():
            all_rows.extend(json.loads(path.read_text()))
    REPORTS.mkdir(parents=True, exist_ok=True)
    (ROOT / "scoring" / "judgments.json").write_text(json.dumps(all_rows, indent=2) + "\n")
    coverage = {name: scores[name] for name in scores}
    (ROOT / "scoring" / "risk_coverage.json").write_text(json.dumps(coverage, indent=2, sort_keys=True) + "\n")
    proof = {
        name: {
            "mean_proof_size": scores[name].get("mean_proof_size"),
            "median_proof_size": scores[name].get("median_proof_size"),
            "proof_validity": scores[name].get("proof_validity"),
            "grounding_validity": scores[name].get("grounding_validity"),
        }
        for name in scores
    }
    (ROOT / "scoring" / "proof_audit.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")

    lines = [
        "# Semantic Proof / Risk-Coverage Benchmark v1",
        "",
        "Mechanism study of bounded identity adjudication. Not Constructor v3.",
        "A0 is imported from frozen Constructor v2 AXIS A. A1–A6 were not prompt-tuned after seeing results.",
        "",
        "```",
        f"{'Strategy':<22} {'Risk':>8} {'Coverage':>10} {'SAME recall':>12} {'Exact':>8}",
    ]
    for name in ORDER:
        if name in scores:
            lines.append(table_line(name, scores[name]))
    lines.extend(
        [
            "```",
            "",
            "Primary question: can any strategy materially increase SAME recall over v2 while retaining zero or near-zero unsupported closure?",
            "",
        ]
    )
    best = None
    for name, score in scores.items():
        if name == "a0_v2":
            continue
        risk = score.get("semantic_risk") or 0
        if risk > 0.05:
            continue
        rec = score.get("SAME_recall") or 0
        if best is None or rec > best[1]:
            best = (name, rec, risk)
    a0 = scores.get("a0_v2") or {}
    lines.append("## MEASURED")
    for name, score in scores.items():
        lines.append(
            f"- **{name}**: unsupported={score.get('unsupported_closures')} "
            f"risk={score.get('semantic_risk')} coverage={score.get('semantic_coverage')} "
            f"exact={score.get('exact_accuracy')} SAME_recall={score.get('SAME_recall')} "
            f"under_closure={score.get('under_closure')} polarity={score.get('polarity_errors')} "
            f"correct_downgraded={score.get('correct_closure_incorrectly_downgraded')} "
            f"SAME_never_proposed={score.get('correct_SAME_never_proposed')} "
            f"compared={score.get('compared')}"
        )
    lines.extend(
        [
            "",
            "## OBSERVED",
            f"- A0 SAME recall={a0.get('SAME_recall')} exact={a0.get('exact_accuracy')} risk={a0.get('semantic_risk')}.",
            f"- Lowest-risk strategy with highest SAME recall among A1–A6: {best}.",
            "",
            "## HYPOTHESIS",
            "- Positive semantic proof remains the binding constraint if SAME recall stays near A0 while risk stays near zero.",
            "- If a strategy raises SAME recall by recovering cue-verifier downgrades without new unsupported closures, the v2 cue list was the bottleneck rather than the model.",
            "",
            f"Frozen at {datetime.now(timezone.utc).isoformat()}.",
            "",
        ]
    )
    payload = {
        "experiment": "semantic-proof-benchmark-v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "strategies": scores,
        "best_low_risk": {"strategy": best[0], "SAME_recall": best[1], "risk": best[2]} if best else None,
    }
    (REPORTS / "semantic_proof_benchmark.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    (REPORTS / "semantic_proof_benchmark.md").write_text("\n".join(lines) + "\n")
    return payload


if __name__ == "__main__":
    write_reports()
    print((REPORTS / "semantic_proof_benchmark.md").read_text()[:3000])
