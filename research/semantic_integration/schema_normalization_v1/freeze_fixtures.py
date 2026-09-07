"""Copy frozen participant Worlds and build certified fixture. Do not alter sources."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
    build_certified_world,
)
from research.semantic_integration.schema_normalization_v1.paths import (
    CERTIFIED,
    PARTICIPANT,
    V2,
)


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def certified_attached_contracts() -> dict:
    """Evaluator-certified consumer interface. Not inferred from constructor names."""
    def roles(*pairs: tuple[str, str]) -> list[dict[str, str]]:
        return [{"role_name": n, "role_type": t, "column_name": n} for n, t in pairs]

    return {
        "invoice_record": {
            "physical_table": "invoice_record",
            "physical_roles": roles(
                ("invoice_id", "TEXT"),
                ("billed_name", "TEXT"),
                ("amount", "REAL"),
                ("currency", "TEXT"),
                ("period", "TEXT"),
                ("status", "TEXT"),
            ),
            "scope": "WORLD",
        },
        "contract_record": {
            "physical_table": "contract_record",
            "physical_roles": roles(("contract_id", "TEXT"), ("counterparty_text", "TEXT")),
            "scope": "WORLD",
        },
        "contract_active": {
            "physical_table": "contract_active",
            "physical_roles": roles(("contract_id", "TEXT"), ("active", "BOOLEAN")),
            "scope": "WORLD",
        },
        "contract_clause_kind": {
            "physical_table": "contract_clause_kind",
            "physical_roles": roles(("contract_id", "TEXT"), ("clause_kind", "TEXT")),
            "dispositions": ["PRESENT", "ABSENT", "UNRESOLVED"],
            "scope": "WORLD",
        },
        "identity_judgment": {
            "physical_table": "identity_judgment",
            "physical_roles": roles(("left", "TEXT"), ("right", "TEXT"), ("disposition", "TEXT")),
            "dispositions": ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"],
            "algebra": {"symmetric": True, "transitive": False},
            "scope": "WORLD",
        },
        "crm_record": {
            "physical_table": "crm_record",
            "physical_roles": roles(("account", "TEXT"), ("account_name", "TEXT")),
            "scope": "WORLD",
        },
        "registry_record": {
            "physical_table": "registry_record",
            "physical_roles": roles(
                ("company_number", "TEXT"),
                ("legal_name", "TEXT"),
                ("status", "TEXT"),
            ),
            "scope": "WORLD",
        },
    }


def freeze_certified() -> Path:
    CERTIFIED.mkdir(parents=True, exist_ok=True)
    dest = CERTIFIED / "world.sqlite"
    build_certified_world(dest)
    from research.semantic_integration.schema_normalization_v1.catalog import connect, roles_from_tv

    contracts = certified_attached_contracts()
    conn = connect(dest)
    try:
        roles = roles_from_tv(conn)
    finally:
        conn.close()
    for table, contract in contracts.items():
        if roles.get(table):
            contract["physical_roles"] = [
                {"role_name": r["role_name"], "role_type": r["role_type"], "column_name": r["column_name"]}
                for r in roles[table]
            ]
    (CERTIFIED / "attached_contracts.json").write_text(json.dumps(contracts, indent=2) + "\n")
    return dest


def freeze_participants() -> dict[str, str]:
    PARTICIPANT.mkdir(parents=True, exist_ok=True)
    fingerprints = {}
    for index in range(1, 6):
        trial = f"T{index}"
        src_world = V2 / "axis_d" / "trials" / trial / "passes" / "p8" / "workspace_snapshot" / "06_world" / "world.sqlite"
        src_vocab = V2 / "axis_d" / "trials" / trial / "passes" / "p1" / "workspace_snapshot" / "01_vocabulary.json"
        src_disp = V2 / "axis_d" / "trials" / trial / "passes" / "p8" / "workspace_snapshot" / "05_dispositions.json"
        dest = PARTICIPANT / trial
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_world, dest / "world.sqlite")
        if src_vocab.exists():
            shutil.copy2(src_vocab, dest / "01_vocabulary.json")
        if src_disp.exists():
            shutil.copy2(src_disp, dest / "05_dispositions.json")
        fingerprints[trial] = sha256_file(dest / "world.sqlite")
    return fingerprints
