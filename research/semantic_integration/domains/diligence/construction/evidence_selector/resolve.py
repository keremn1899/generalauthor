"""C3 bounded resolution of semantic frontier obligations."""

from __future__ import annotations

from taskview import Grounding, GroundingKind, TaskView

# Grounded resolutions: disposition is SAME_ENTITY, DISTINCT, or UNRESOLVED.
RESOLUTIONS: list[tuple[str, str, str, list[Grounding]]] = [
    (
        "crm:HEL-441",
        "billing:Helion Robotics Limited",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "Helion Robotics Ltd operating name; invoices use Limited form",
            )
        ],
    ),
    (
        "billing:Helion Robotics Limited",
        "registry:11847201",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "company_registry.csv",
                "HELION ROBOTICS LIMITED",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "same legal entity",
            ),
        ],
    ),
    (
        "crm:HEL-441",
        "registry:11847201",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.WORLD,
                "identity_judgment",
                "transitive via billing",
            )
        ],
    ),
    (
        "crm:HEL-441",
        "contract:MSA-HELION-2019",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-HELION-2019.md",
                "counterparty Helion Robotics Ltd.",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "crm.csv",
                "HEL-441 Helion Robotics Ltd",
            ),
        ],
    ),
    (
        "billing:Helion Robotics Limited",
        "contract:MSA-HELION-2019",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-HELION-2019.md",
                "counterparty Helion Robotics Ltd.",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "billing/invoices.json",
                "Helion Robotics Limited",
            ),
        ],
    ),
    (
        "registry:11847201",
        "registry:11847299",
        "DISTINCT",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "Helion Industrial Systems Ltd is a different company",
            )
        ],
    ),
    (
        "crm:NBA-102",
        "billing:Northbridge Analytics Inc.",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "sales short name vs billing Inc. form",
            )
        ],
    ),
    (
        "billing:Northbridge Analytics Inc.",
        "registry:3840192",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "company_registry.csv",
                "NORTHBRIDGE ANALYTICS INC",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-NBA-2021.md",
                "counterparty Northbridge Analytics, Inc.",
            ),
        ],
    ),
    (
        "billing:Northbridge Analytics Inc.",
        "registry:2019-0008841",
        "UNRESOLVED",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "Legal has not determined which registry entity is contracting party",
            )
        ],
    ),
    (
        "crm:NBA-102",
        "registry:3840192",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.WORLD,
                "identity_judgment",
                "transitive via billing",
            )
        ],
    ),
    (
        "crm:NBA-102",
        "registry:2019-0008841",
        "UNRESOLVED",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "registry link unresolved",
            )
        ],
    ),
    (
        "crm:NBA-102",
        "contract:MSA-NBA-2021",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-NBA-2021.md",
                "counterparty Northbridge Analytics, Inc.",
            )
        ],
    ),
    (
        "billing:Northbridge Analytics Inc.",
        "contract:MSA-NBA-2021",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-NBA-2021.md",
                "counterparty Northbridge Analytics, Inc.",
            )
        ],
    ),
    (
        "crm:OAK-77",
        "billing:Oakfield Logistik GmbH",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "rebrand 2023; register number unchanged",
            )
        ],
    ),
    (
        "billing:Oakfield Logistik GmbH",
        "registry:HRB 88421",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "company_registry.csv",
                "Oakfield Logistik GmbH",
            )
        ],
    ),
    (
        "crm:OAK-77",
        "registry:HRB 88421",
        "SAME_ENTITY",
        [
            Grounding(GroundingKind.WORLD, "identity_judgment", "transitive via billing")
        ],
    ),
    (
        "crm:OAK-77",
        "contract:MSA-OAK-2018",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "rebrand; same entity as Oakfield Logistics GmbH counterparty",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-OAK-2018.md",
                "counterparty Oakfield Logistics GmbH",
            ),
        ],
    ),
    (
        "billing:Oakfield Logistik GmbH",
        "contract:MSA-OAK-2018",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "rebrand from Oakfield Logistics GmbH",
            )
        ],
    ),
    (
        "crm:MER-55",
        "billing:Meridian Energy Partners LLC",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "Meridian advisory retainer under MSA-MER-2024",
            )
        ],
    ),
    (
        "billing:Meridian Energy Partners LLC",
        "registry:4721193",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "company_registry.csv",
                "MERIDIAN ENERGY PARTNERS LLC",
            )
        ],
    ),
    (
        "crm:MER-55",
        "registry:4721193",
        "SAME_ENTITY",
        [
            Grounding(GroundingKind.WORLD, "identity_judgment", "transitive via billing")
        ],
    ),
    (
        "crm:MER-55",
        "contract:MSA-MER-2024",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "commercial_notes.md",
                "advisory retainer under MSA-MER-2024",
            )
        ],
    ),
    (
        "billing:Meridian Energy Partners LLC",
        "contract:MSA-MER-2024",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/MSA-MER-2024.md",
                "counterparty Meridian Energy Partners LLC",
            )
        ],
    ),
    (
        "crm:VEL-19",
        "billing:Vellum Print Co Ltd",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "crm.csv",
                "VEL-19 Vellum Print Co",
            ),
            Grounding(
                GroundingKind.SOURCE,
                "billing/invoices.json",
                "Vellum Print Co Ltd",
            ),
        ],
    ),
    (
        "billing:Vellum Print Co Ltd",
        "registry:09338441",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "company_registry.csv",
                "VELLUM PRINT CO LTD",
            )
        ],
    ),
    (
        "crm:VEL-19",
        "registry:09338441",
        "SAME_ENTITY",
        [
            Grounding(GroundingKind.WORLD, "identity_judgment", "transitive via billing")
        ],
    ),
    (
        "crm:VEL-19",
        "contract:SOW-VEL-2022",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/SOW-VEL-2022.md",
                "counterparty Vellum Print Co Ltd",
            )
        ],
    ),
    (
        "billing:Vellum Print Co Ltd",
        "contract:SOW-VEL-2022",
        "SAME_ENTITY",
        [
            Grounding(
                GroundingKind.SOURCE,
                "sources/contracts/SOW-VEL-2022.md",
                "counterparty Vellum Print Co Ltd",
            )
        ],
    ),
]


def apply_resolutions(tv: TaskView) -> list[dict]:
    obligations_export: list[dict] = []
    for left, right, disposition, grounds in RESOLUTIONS:
        tv.assert_tuple(
            "identity_judgment",
            {"left": left, "right": right, "disposition": disposition},
            grounding=grounds,
        )
        obligations_export.append(
            {
                "relation": "identity_judgment",
                "values": {"left": left, "right": right},
                "judgment": disposition,
                "evidence": [f"{g.kind.value}:{g.reference}" for g in grounds],
            }
        )
    return obligations_export
