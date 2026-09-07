"""Write Probe B markdown from frozen JSON. No rerun."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from research.semantic_integration.schema_normalization_v1.paths import REPORTS


def write_report(payload: dict | None = None) -> None:
    if payload is None:
        payload = json.loads((REPORTS / "schema_normalization.json").read_text())
    b0 = payload["b0"]
    meta = payload.get("metamorphic") or {}
    lines = [
        "# Contract-Driven Schema Normalization Benchmark v1",
        "",
        "Schema/IR compilation. No semantic adjudication. Not Constructor v3.",
        "",
        "## B0 — exact contracts",
        "",
        f"Certified World A/B/C/D exact after normalization: {b0['certified']['world_correctness']['all_exact']}",
        f"Certified recovered: {b0['certified']['normalization']['canonical_relations_recovered']}",
        f"Certified missed: {b0['certified']['normalization']['required_mappings_missed']}",
        "",
        "Participant Worlds (normalization vs raw projector vs hidden expected):",
        "",
    ]
    for trial, item in b0["participants"].items():
        wc = item["world_correctness"]
        raw = item.get("raw_projector") or {}
        lines.append(
            f"- **{trial}** recovered={item['normalization']['canonical_relations_recovered']} "
            f"missed={item['normalization']['required_mappings_missed']} "
            f"normalized A/B/C/D={wc['A_exact']}/{wc['B_exact']}/{wc['C_exact']}/{wc['D_exact']} "
            f"raw A/B/C/D={raw.get('A_exact')}/{raw.get('B_exact')}/{raw.get('C_exact')}/{raw.get('D_exact')}"
        )
    lines.extend(["", "## Metamorphic (certified World)", ""])
    lines.append("```")
    lines.append(f"{'Class':<22} {'equiv':>8} {'A/B/C/D exact':>16}")
    for name, item in meta.items():
        wc = item.get("world_correctness") or {}
        exact = f"{wc.get('A_exact')}/{wc.get('B_exact')}/{wc.get('C_exact')}/{wc.get('D_exact')}"
        lines.append(
            f"{name:<22} {str(item.get('behavioral_equivalence_to_certified_normalized')):>8} {exact:>16}"
        )
    lines.extend(
        [
            "```",
            "",
            "## MEASURED",
            f"- Semantic-family hints tested: {payload.get('semantic_family_tested')}",
            "",
            "## OBSERVED",
            "- Participant vocabularies are factored and role-named differently from the certified consumer interface.",
            "- Metamorphic classes that preserve attached role identity should be mechanically normalizable; decomposition and epistemic split are harder.",
            "",
            "## HYPOTHESIS",
            "- If certified B0 is exact and B1–B4 equivalent, exact contracts suffice for rename/orientation/physical layout.",
            "- If participant A/B/C/D remain inexact after normalization, remaining error is World content, not interface compilation — or missing role-identity in contracts.",
            "",
            f"Frozen at {payload.get('frozen_at') or datetime.now(timezone.utc).isoformat()}.",
            "",
        ]
    )
    (REPORTS / "schema_normalization.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    write_report()
