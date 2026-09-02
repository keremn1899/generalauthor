"""C2/C3 semantic frontier and grounded resolutions."""

from __future__ import annotations

import json
from pathlib import Path

from taskview import Grounding, GroundingKind, RelationMode, Role, RoleType, TaskView

ROOT = Path(__file__).resolve().parents[2]


def _methods(detail: str) -> list[Grounding]:
    return [Grounding(GroundingKind.SOURCE, "methods_notes.md", detail)]


def _declare_semantic_relations(tv: TaskView) -> None:
    tv.declare_relation(
        "study_identity_judgment",
        [
            Role("left", RoleType.REFERENT),
            Role("right", RoleType.REFERENT),
            Role("disposition", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Grounded judgment whether two records refer to the same underlying study.",
    )
    tv.declare_relation(
        "outcome_correspondence_judgment",
        [
            Role("study", RoleType.REFERENT),
            Role("publication", RoleType.REFERENT),
            Role("disposition", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Grounded judgment of registered versus reported primary outcome correspondence.",
    )
    tv.declare_relation(
        "variable_sufficiency_judgment",
        [
            Role("study", RoleType.REFERENT),
            Role("dataset", RoleType.REFERENT),
            Role("disposition", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Grounded judgment of dataset variable sufficiency for registered primary outcome.",
    )


STUDY_IDENTITY_RESOLUTIONS: list[dict] = [
    {
        "left": "registry:REG-2021-0412",
        "right": "publication:PUB-CLEAR-2023",
        "judgment": "ACCEPT",
        "evidence": "publications.json registry_id REG-2021-0412",
    },
    {
        "left": "registry:REG-2019-1108",
        "right": "publication:PUB-AURORA-2022",
        "judgment": "ACCEPT",
        "evidence": "publications.json trial_registration REG-2019-1108",
    },
    {
        "left": "registry:REG-2022-0094",
        "right": "publication:PUB-HELIOS-2023",
        "judgment": "ACCEPT",
        "evidence": "publications.json registry_id REG-2022-0094",
    },
    {
        "left": "registry:REG-2021-2204",
        "right": "publication:PUB-MARLIN-2023",
        "judgment": "ACCEPT",
        "evidence": "publications.json registration REG-2021-2204",
    },
    {
        "left": "registry:REG-2021-2204",
        "right": "publication:PUB-MARLIN-AUDIT-2022",
        "judgment": "REJECT",
        "evidence": "methods_notes.md MARLIN audit is retrospective quality report, not MARLIN trial",
    },
    {
        "left": "registry:REG-2021-0412",
        "right": "dataset:DS-CLEAR-HTN-V2",
        "judgment": "ACCEPT",
        "evidence": "datasets.csv linked_registry REG-2021-0412",
    },
    {
        "left": "registry:REG-2019-1108",
        "right": "dataset:DS-AURORA-CORE",
        "judgment": "ACCEPT",
        "evidence": "datasets.csv linked_registry REG-2019-1108",
    },
    {
        "left": "registry:REG-2022-0094",
        "right": "dataset:DS-HELIOS-SLP",
        "judgment": "ACCEPT",
        "evidence": "datasets.csv linked_registry REG-2022-0094",
    },
    {
        "left": "registry:REG-2021-2204",
        "right": "dataset:DS-MARLIN-LAB",
        "judgment": "ACCEPT",
        "evidence": "datasets.csv linked_registry REG-2021-2204",
    },
    {
        "left": "registry:REG-2023-0155",
        "right": "dataset:DS-PINE-SCREEN",
        "judgment": "ACCEPT",
        "evidence": "datasets.csv linked_registry REG-2023-0155",
    },
    {
        "left": "publication:PUB-NW-2023",
        "right": "dataset:DS-NW-PULM",
        "judgment": "ACCEPT",
        "evidence": "shared protocol NW-PULM-24 and matching n=148",
    },
    {
        "left": "registry:REG-2020-0771",
        "right": "publication:PUB-NW-2023",
        "judgment": "UNRESOLVED",
        "evidence": "methods_notes.md NORTHWIND publication/dataset not uniquely bound to RCT registry",
    },
    {
        "left": "registry:REG-2018-3301",
        "right": "publication:PUB-NW-2023",
        "judgment": "UNRESOLVED",
        "evidence": "methods_notes.md observational cohort vs RCT; shared branding not identity",
    },
    {
        "left": "registry:REG-2020-0771",
        "right": "dataset:DS-NW-PULM",
        "judgment": "UNRESOLVED",
        "evidence": "NW-PULM-variables.md deposit label does not name registry id",
    },
    {
        "left": "registry:REG-2018-3301",
        "right": "dataset:DS-NW-PULM",
        "judgment": "UNRESOLVED",
        "evidence": "NW-PULM-variables.md deposit label does not name registry id",
    },
    {
        "left": "registry:REG-2020-0771",
        "right": "registry:REG-2018-3301",
        "judgment": "REJECT",
        "evidence": "methods_notes.md two distinct NORTHWIND programmes (RCT vs observational cohort)",
    },
    {
        "left": "publication:PUB-MARLIN-AUDIT-2022",
        "right": "dataset:DS-MARLIN-LAB",
        "judgment": "REJECT",
        "evidence": "methods_notes.md audit is not the MARLIN randomised trial dataset",
    },
]

OUTCOME_CORRESPONDENCE_RESOLUTIONS: list[dict] = [
    {
        "study": "registry:REG-2021-0412",
        "publication": "publication:PUB-CLEAR-2023",
        "judgment": "ACCEPT",
        "evidence": "methods_notes.md registry systolic pressure equals paper SBP change; sbp_delta_12 in codebook",
    },
    {
        "study": "registry:REG-2019-1108",
        "publication": "publication:PUB-AURORA-2022",
        "judgment": "ACCEPT",
        "evidence": "methods_notes.md registered and published primary is HbA1c at 26 weeks",
    },
    {
        "study": "registry:REG-2021-2204",
        "publication": "publication:PUB-MARLIN-2023",
        "judgment": "ACCEPT",
        "evidence": "methods_notes.md and matching percent LDL at 12 weeks wording",
    },
    {
        "study": "registry:REG-2022-0094",
        "publication": "publication:PUB-HELIOS-2023",
        "judgment": "REJECT",
        "evidence": "methods_notes.md PSQI registered; publication primary is sleep latency, not wording variant",
    },
]

VARIABLE_SUFFICIENCY_RESOLUTIONS: list[dict] = [
    {
        "study": "registry:REG-2021-0412",
        "dataset": "dataset:DS-CLEAR-HTN-V2",
        "judgment": "ACCEPT",
        "evidence": "CLEAR-HTN-variables.md sbp_delta_12 week-12 systolic minus baseline",
    },
    {
        "study": "registry:REG-2019-1108",
        "dataset": "dataset:DS-AURORA-CORE",
        "judgment": "REJECT",
        "evidence": "methods_notes.md and AURORA-variables.md no HbA1c in deposit",
    },
    {
        "study": "registry:REG-2022-0094",
        "dataset": "dataset:DS-HELIOS-SLP",
        "judgment": "ACCEPT",
        "evidence": "HELIOS-variables.md psqi_total_bl and psqi_total_w8 for registered PSQI endpoint",
    },
    {
        "study": "registry:REG-2021-2204",
        "dataset": "dataset:DS-MARLIN-LAB",
        "judgment": "ACCEPT",
        "evidence": "MARLIN-variables.md ldl_pct_change_12 percent change at week 12",
    },
    {
        "study": "registry:REG-2023-0155",
        "dataset": "dataset:DS-PINE-SCREEN",
        "judgment": "REJECT",
        "evidence": "methods_notes.md and PINE-variables.md screening log only; no week-4 TNSS",
    },
]


def apply_resolutions(tv: TaskView) -> list[dict]:
    _declare_semantic_relations(tv)
    obligations: list[dict] = []

    for item in STUDY_IDENTITY_RESOLUTIONS:
        left, right = sorted((item["left"], item["right"]))
        tv.assert_tuple(
            "study_identity_judgment",
            {"left": left, "right": right, "disposition": item["judgment"]},
            grounding=_methods(item["evidence"]),
        )
        obligations.append(
            {
                "relation": "study_identity_judgment",
                "values": {"left": left, "right": right, "disposition": item["judgment"]},
                "judgment": item["judgment"],
                "evidence": item["evidence"],
            }
        )

    for item in OUTCOME_CORRESPONDENCE_RESOLUTIONS:
        tv.assert_tuple(
            "outcome_correspondence_judgment",
            {
                "study": item["study"],
                "publication": item["publication"],
                "disposition": item["judgment"],
            },
            grounding=_methods(item["evidence"]),
        )
        obligations.append(
            {
                "relation": "outcome_correspondence_judgment",
                "values": {
                    "study": item["study"],
                    "publication": item["publication"],
                    "disposition": item["judgment"],
                },
                "judgment": item["judgment"],
                "evidence": item["evidence"],
            }
        )

    for item in VARIABLE_SUFFICIENCY_RESOLUTIONS:
        tv.assert_tuple(
            "variable_sufficiency_judgment",
            {
                "study": item["study"],
                "dataset": item["dataset"],
                "disposition": item["judgment"],
            },
            grounding=_methods(item["evidence"]),
        )
        obligations.append(
            {
                "relation": "variable_sufficiency_judgment",
                "values": {
                    "study": item["study"],
                    "dataset": item["dataset"],
                    "disposition": item["judgment"],
                },
                "judgment": item["judgment"],
                "evidence": item["evidence"],
            }
        )

    for row in tv.query(
        """
        SELECT left_id, right_id, basis FROM identity_candidate c
        WHERE NOT EXISTS (
          SELECT 1 FROM study_identity_judgment j
          WHERE j.left_id = c.left_id AND j.right_id = c.right_id
        )
        """
    ):
        obligations.append(
            {
                "relation": "study_identity_judgment",
                "values": {"left": row["left_id"], "right": row["right_id"]},
                "judgment": "UNRESOLVED",
                "evidence": f"mechanical candidate only: {row['basis']}",
            }
        )

    return obligations


def write_obligations(obligations: list[dict]) -> None:
    path = ROOT / "world" / "obligations.json"
    path.write_text(json.dumps(obligations, indent=2) + "\n", encoding="utf-8")
