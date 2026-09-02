"""C0/C1 mechanical compilation from heterogeneous sources into TaskView."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from taskview import Grounding, GroundingKind, RelationMode, Role, RoleType, TaskView

ROOT = Path(__file__).resolve().parents[2]
SOURCES = ROOT / "sources"
SUPPLEMENTS = SOURCES / "supplements"

CODEBOOK_DATASET = {
    "CLEAR-HTN-variables.md": "dataset:DS-CLEAR-HTN-V2",
    "AURORA-variables.md": "dataset:DS-AURORA-CORE",
    "NW-PULM-variables.md": "dataset:DS-NW-PULM",
    "HELIOS-variables.md": "dataset:DS-HELIOS-SLP",
    "MARLIN-variables.md": "dataset:DS-MARLIN-LAB",
    "PINE-variables.md": "dataset:DS-PINE-SCREEN",
}


def _src(ref: str, detail: str = "") -> list[Grounding]:
    return [Grounding(GroundingKind.SOURCE, ref, detail)]


def _registry_id(raw: str) -> str:
    return f"registry:{raw}"


def _publication_id(raw: str) -> str:
    return f"publication:{raw}"


def _dataset_id(raw: str) -> str:
    return f"dataset:{raw}"


def _declare_world_relations(tv: TaskView) -> None:
    tv.declare_relation(
        "registered_primary_outcome",
        [Role("study", RoleType.REFERENT), Role("outcome_text", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Registered primary outcome wording from the study registry.",
    )
    tv.declare_relation(
        "publication_reported_primary",
        [Role("publication", RoleType.REFERENT), Role("outcome_text", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Primary outcome wording reported in a publication record.",
    )
    tv.declare_relation(
        "publication_stated_registry_id",
        [
            Role("publication", RoleType.REFERENT),
            Role("study", RoleType.REFERENT),
            Role("field_name", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Exact registry identifier string carried by a publication record.",
    )
    tv.declare_relation(
        "dataset_stated_registry_link",
        [Role("dataset", RoleType.REFERENT), Role("study", RoleType.REFERENT)],
        mode=RelationMode.BASE,
        description="Registry identifier listed on a dataset deposit record.",
    )
    tv.declare_relation(
        "dataset_protocol_code",
        [Role("dataset", RoleType.REFERENT), Role("code", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Protocol code label on a dataset deposit.",
    )
    tv.declare_relation(
        "publication_protocol_code",
        [Role("publication", RoleType.REFERENT), Role("code", RoleType.TEXT)],
        mode=RelationMode.BASE,
        description="Local protocol code cited by a publication.",
    )
    tv.declare_relation(
        "dataset_row_count",
        [Role("dataset", RoleType.REFERENT), Role("n_rows", RoleType.INTEGER)],
        mode=RelationMode.BASE,
        description="Row count on a deposited dataset file.",
    )
    tv.declare_relation(
        "publication_n_analysed",
        [Role("publication", RoleType.REFERENT), Role("n_analysed", RoleType.INTEGER)],
        mode=RelationMode.BASE,
        description="Analysed sample size reported by a publication.",
    )
    tv.declare_relation(
        "dataset_variable",
        [
            Role("dataset", RoleType.REFERENT),
            Role("variable", RoleType.TEXT),
            Role("description", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Variable name and description from a dataset codebook.",
    )
    tv.declare_relation(
        "identity_candidate",
        [
            Role("left", RoleType.REFERENT),
            Role("right", RoleType.REFERENT),
            Role("basis", RoleType.TEXT),
        ],
        mode=RelationMode.BASE,
        description="Mechanical same-study candidate link before semantic judgment.",
    )
    tv.declare_relation(
        "outcome_correspondence_candidate",
        [Role("study", RoleType.REFERENT), Role("publication", RoleType.REFERENT)],
        mode=RelationMode.BASE,
        description="Registry/publication pair linked by identity candidate or stated id.",
    )


def _parse_codebook(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|") or line.startswith("|---") or "variable" in line:
            continue
        parts = [part.strip() for part in line.strip("|").split("|")]
        if len(parts) >= 2 and parts[0] and parts[0] != "variable":
            rows.append((parts[0], parts[1]))
    return rows


def _emit_identity_candidates(tv: TaskView) -> None:
    def candidate(left: str, right: str, basis: str) -> None:
        pair = sorted((left, right))
        tv.assert_tuple(
            "identity_candidate",
            {"left": pair[0], "right": pair[1], "basis": basis},
            grounding=_src("mechanical_compiler", basis),
        )

    for row in tv.query(
        "SELECT publication_id, study_id, field_name "
        "FROM publication_stated_registry_id"
    ):
        candidate(
            row["publication_id"],
            row["study_id"],
            f"publication_stated_registry_id:{row['field_name']}",
        )

    for row in tv.query(
        "SELECT dataset_id, study_id FROM dataset_stated_registry_link"
    ):
        candidate(row["dataset_id"], row["study_id"], "dataset_stated_registry_link")

    for row in tv.query(
        """
        SELECT p.publication_id AS left_id, d.dataset_id AS right_id
        FROM publication_protocol_code p
        JOIN dataset_protocol_code d ON p.code = d.code
        """
    ):
        candidate(row["left_id"], row["right_id"], "shared_protocol_code")

    for row in tv.query(
        """
        SELECT p.publication_id AS left_id, d.dataset_id AS right_id
        FROM publication_n_analysed p
        JOIN dataset_row_count d ON p.n_analysed = d.n_rows
        JOIN publication_protocol_code pc ON pc.publication_id = p.publication_id
        JOIN dataset_protocol_code dc
          ON dc.dataset_id = d.dataset_id AND dc.code = pc.code
        """
    ):
        candidate(row["left_id"], row["right_id"], "protocol_code_and_matching_n")

    northwind = [
        row["study_id"]
        for row in tv.query(
            "SELECT study_id FROM registered_primary_outcome "
            "WHERE study_id LIKE '%REG-2020-0771%' OR study_id LIKE '%REG-2018-3301%'"
        )
    ]
    if len(northwind) == 2:
        candidate(northwind[0], northwind[1], "shared_programme_name")


def _emit_outcome_candidates(tv: TaskView) -> None:
    for row in tv.query(
        "SELECT publication_id, study_id FROM publication_stated_registry_id"
    ):
        tv.assert_tuple(
            "outcome_correspondence_candidate",
            {"study": row["study_id"], "publication": row["publication_id"]},
            grounding=_src("mechanical_compiler", "stated_registry_id"),
        )


def compile_sources(tv: TaskView) -> list[str]:
    """Return sorted registry ids compiled from sources."""

    _declare_world_relations(tv)
    registry_ids: list[str] = []

    with (SOURCES / "study_registry.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            rid = row["registry_id"]
            registry_ids.append(rid)
            study = _registry_id(rid)
            tv.add_referent(
                study,
                label=row["short_title"],
                grounding=_src("study_registry.csv", f"registry_id={rid}"),
            )
            tv.assert_tuple(
                "registered_primary_outcome",
                {"study": study, "outcome_text": row["primary_outcome"]},
                grounding=_src("study_registry.csv", f"{rid}.primary_outcome"),
            )

    publications = json.loads((SOURCES / "publications.json").read_text(encoding="utf-8"))
    registry_fields = ("registry_id", "trial_registration", "registration")
    for pub in publications:
        pid = pub["publication_id"]
        publication = _publication_id(pid)
        tv.add_referent(
            publication,
            label=pub["title"],
            grounding=_src("publications.json", f"publication_id={pid}"),
        )
        tv.assert_tuple(
            "publication_reported_primary",
            {"publication": publication, "outcome_text": pub["reported_primary"]},
            grounding=_src("publications.json", f"{pid}.reported_primary"),
        )
        tv.assert_tuple(
            "publication_n_analysed",
            {"publication": publication, "n_analysed": int(pub["n_analysed"])},
            grounding=_src("publications.json", f"{pid}.n_analysed"),
        )
        for field in registry_fields:
            if field in pub:
                tv.assert_tuple(
                    "publication_stated_registry_id",
                    {
                        "publication": publication,
                        "study": _registry_id(pub[field]),
                        "field_name": field,
                    },
                    grounding=_src("publications.json", f"{pid}.{field}"),
                )
        if "local_protocol" in pub:
            tv.assert_tuple(
                "publication_protocol_code",
                {"publication": publication, "code": pub["local_protocol"]},
                grounding=_src("publications.json", f"{pid}.local_protocol"),
            )

    with (SOURCES / "datasets.csv").open(encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            did = row["dataset_id"]
            dataset = _dataset_id(did)
            tv.add_referent(
                dataset,
                label=row["title"],
                grounding=_src("datasets.csv", f"dataset_id={did}"),
            )
            tv.assert_tuple(
                "dataset_row_count",
                {"dataset": dataset, "n_rows": int(row["n_rows"])},
                grounding=_src("datasets.csv", f"{did}.n_rows"),
            )
            if row["protocol_code"]:
                tv.assert_tuple(
                    "dataset_protocol_code",
                    {"dataset": dataset, "code": row["protocol_code"]},
                    grounding=_src("datasets.csv", f"{did}.protocol_code"),
                )
            if row["linked_registry"]:
                tv.assert_tuple(
                    "dataset_stated_registry_link",
                    {
                        "dataset": dataset,
                        "study": _registry_id(row["linked_registry"]),
                    },
                    grounding=_src("datasets.csv", f"{did}.linked_registry"),
                )

    for filename, dataset in CODEBOOK_DATASET.items():
        path = SUPPLEMENTS / filename
        for variable, description in _parse_codebook(path):
            tv.assert_tuple(
                "dataset_variable",
                {"dataset": dataset, "variable": variable, "description": description},
                grounding=_src(f"supplements/{filename}", variable),
            )

    _emit_identity_candidates(tv)
    _emit_outcome_candidates(tv)
    return sorted(registry_ids)
