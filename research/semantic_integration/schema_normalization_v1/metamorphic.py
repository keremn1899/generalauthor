"""Metamorphic World generators. Fixed seed. Semantics-preserving by construction."""

from __future__ import annotations

import hashlib
import json
import random
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from research.semantic_integration.schema_normalization_v1.catalog import roles_from_tv, table_names
from research.semantic_integration.schema_normalization_v1.paths import METAMORPHIC, SEED


def _rng(label: str) -> random.Random:
    material = f"{SEED}:{label}".encode()
    return random.Random(int(hashlib.sha256(material).hexdigest()[:16], 16))


def _copy_world(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    shutil.copy2(src, dest)


def _attach(dest: Path, contracts: dict[str, Any]) -> None:
    (dest.parent / "attached_contracts.json").write_text(json.dumps(contracts, indent=2) + "\n")


def _load_base_contracts(world: Path) -> dict[str, Any]:
    conn = sqlite3.connect(str(world))
    conn.row_factory = sqlite3.Row
    roles = roles_from_tv(conn)
    tables = table_names(conn)
    conn.close()
    attached = {}
    for table in tables:
        role_list = roles.get(table) or []
        dispositions = []
        if table == "identity_judgment":
            dispositions = ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"]
        attached[table] = {
            "physical_table": table,
            "physical_roles": role_list,
            "dispositions": dispositions,
            "scope": "WORLD",
        }
        if table == "identity_judgment":
            attached[table]["algebra"] = {"symmetric": True, "transitive": False}
            attached[table]["epistemic_contract"] = {
                "positive_disposition": "SAME_ENTITY",
                "negative_disposition": "DISTINCT",
                "unresolved_disposition": "UNRESOLVED",
            }
        if table == "contract_clause_kind":
            attached[table]["dispositions"] = ["PRESENT", "ABSENT", "UNRESOLVED"]
    return attached


def rename_tables(src: Path, dest: Path, label: str) -> dict[str, str]:
    _copy_world(src, dest)
    rng = _rng(label)
    conn = sqlite3.connect(str(dest))
    mapping = {}
    for table in table_names(conn):
        new = f"rel_{rng.randbytes(4).hex()}"
        mapping[table] = new
        conn.execute(f'ALTER TABLE "{table}" RENAME TO "{new}"')
        conn.execute("UPDATE _tv_relations SET name=? WHERE name=?", (new, table))
        conn.execute("UPDATE _tv_roles SET relation_name=? WHERE relation_name=?", (new, table))
        try:
            conn.execute("UPDATE _tv_assertions SET relation_name=? WHERE relation_name=?", (new, table))
        except sqlite3.Error:
            pass
    conn.commit()
    roles = roles_from_tv(conn)
    conn.close()
    contracts = {}
    base = _load_base_contracts(src)
    for old, new in mapping.items():
        contract = dict(base.get(old) or {})
        contract["physical_table"] = new
        contract["physical_roles"] = roles.get(new) or contract.get("physical_roles") or []
        # preserve identity contract semantics despite physical rename
        if old == "identity_judgment":
            contract["dispositions"] = ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"]
            contract["physical_roles"] = [
                {"role_name": r["role_name"], "role_type": r["role_type"], "column_name": r["column_name"]}
                for r in (roles.get(new) or [])
            ]
        contracts[new] = contract
    # re-read roles after rename
    conn = sqlite3.connect(str(dest))
    roles = roles_from_tv(conn)
    conn.close()
    for new, contract in contracts.items():
        if roles.get(new):
            contract["physical_roles"] = [
                {"role_name": r["role_name"], "role_type": r["role_type"], "column_name": r["column_name"]}
                for r in roles[new]
            ]
    _attach(dest, contracts)
    (dest.parent / "rename_map.json").write_text(json.dumps(mapping, indent=2) + "\n")
    return mapping


def rename_roles(src: Path, dest: Path, label: str) -> dict[str, Any]:
    _copy_world(src, dest)
    rng = _rng(label)
    conn = sqlite3.connect(str(dest))
    roles = roles_from_tv(conn)
    mapping = {}
    for table, role_list in roles.items():
        new_roles = []
        for item in role_list:
            new_role = f"role_{rng.randbytes(3).hex()}"
            mapping[f"{table}.{item['role_name']}"] = {
                "role_id": item["role_name"],
                "surface": new_role,
                "column": item["column_name"],
            }
            new_roles.append(
                {
                    "role_name": item["role_name"],  # identity preserved in contract
                    "role_type": item["role_type"],
                    "column_name": item["column_name"],
                    "surface_role_name": new_role,
                }
            )
        roles[table] = new_roles
    conn.close()
    base = _load_base_contracts(src)
    contracts = {}
    for table, contract in base.items():
        contract = dict(contract)
        contract["physical_roles"] = roles.get(table) or contract.get("physical_roles") or []
        contracts[table] = contract
    _attach(dest, contracts)
    (dest.parent / "role_map.json").write_text(json.dumps(mapping, indent=2) + "\n")
    return mapping


def swap_orientation(src: Path, dest: Path) -> None:
    _copy_world(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("ALTER TABLE identity_judgment RENAME COLUMN left TO col_b")
    conn.execute("ALTER TABLE identity_judgment RENAME COLUMN right TO col_a")
    conn.execute("UPDATE _tv_roles SET column_name='col_b' WHERE relation_name='identity_judgment' AND role_name='left'")
    conn.execute("UPDATE _tv_roles SET column_name='col_a' WHERE relation_name='identity_judgment' AND role_name='right'")
    conn.commit()
    roles = roles_from_tv(conn)
    conn.close()
    contracts = _load_base_contracts(src)
    contracts["identity_judgment"]["physical_roles"] = [
        {"role_name": r["role_name"], "role_type": r["role_type"], "column_name": r["column_name"]}
        for r in roles.get("identity_judgment", [])
    ]
    _attach(dest, contracts)


def physical_layout(src: Path, dest: Path) -> None:
    _copy_world(src, dest)
    conn = sqlite3.connect(str(dest))
    # prefix-stripped copies already in projector; here recreate invoice_record with column order shuffled
    conn.execute(
        "CREATE TABLE invoice_record_phys AS SELECT status, period, currency, amount, billed_name, invoice_id FROM invoice_record"
    )
    conn.execute("DROP TABLE invoice_record")
    conn.execute("ALTER TABLE invoice_record_phys RENAME TO invoice_record")
    conn.execute("UPDATE _tv_roles SET column_name=column_name WHERE relation_name='invoice_record'")
    conn.commit()
    roles = roles_from_tv(conn)
    conn.close()
    contracts = _load_base_contracts(src)
    for table, contract in contracts.items():
        if roles.get(table):
            contract["physical_roles"] = [
                {"role_name": r["role_name"], "role_type": r["role_type"], "column_name": r["column_name"]}
                for r in roles[table]
            ]
    _attach(dest, contracts)


def epistemic_split(src: Path, dest: Path) -> None:
    _copy_world(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("CREATE TABLE same_entity (left TEXT, right TEXT)")
    conn.execute("CREATE TABLE distinct_entity (left TEXT, right TEXT)")
    conn.execute("CREATE TABLE unresolved_entity (left TEXT, right TEXT)")
    conn.execute("INSERT INTO same_entity SELECT left, right FROM identity_judgment WHERE disposition='SAME_ENTITY'")
    conn.execute("INSERT INTO distinct_entity SELECT left, right FROM identity_judgment WHERE disposition='DISTINCT'")
    conn.execute("INSERT INTO unresolved_entity SELECT left, right FROM identity_judgment WHERE disposition='UNRESOLVED'")
    conn.execute("DROP TABLE identity_judgment")
    conn.commit()
    conn.close()
    contracts = _load_base_contracts(src)
    contracts.pop("identity_judgment", None)
    shared_roles = [
        {"role_name": "left", "role_type": "TEXT", "column_name": "left"},
        {"role_name": "right", "role_type": "TEXT", "column_name": "right"},
    ]
    for table, disp in (
        ("same_entity", "SAME_ENTITY"),
        ("distinct_entity", "DISTINCT"),
        ("unresolved_entity", "UNRESOLVED"),
    ):
        contracts[table] = {
            "physical_table": table,
            "physical_roles": shared_roles + [{"role_name": "disposition", "role_type": "TEXT", "column_name": None}],
            "dispositions": ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"],
            "fixed_disposition": disp,
            "algebra": {"symmetric": True, "transitive": False},
            "scope": "WORLD",
        }
    _attach(dest, contracts)


def decompose_invoices(src: Path, dest: Path) -> None:
    _copy_world(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("CREATE TABLE invoice_billed (invoice TEXT, billed_name TEXT)")
    conn.execute("CREATE TABLE invoice_amount (invoice TEXT, amount REAL)")
    conn.execute("CREATE TABLE invoice_currency (invoice TEXT, currency TEXT)")
    conn.execute("CREATE TABLE invoice_period (invoice TEXT, period TEXT)")
    conn.execute("CREATE TABLE invoice_status (invoice TEXT, status TEXT)")
    conn.execute("INSERT INTO invoice_billed SELECT invoice_id, billed_name FROM invoice_record")
    conn.execute("INSERT INTO invoice_amount SELECT invoice_id, amount FROM invoice_record")
    conn.execute("INSERT INTO invoice_currency SELECT invoice_id, currency FROM invoice_record")
    conn.execute("INSERT INTO invoice_period SELECT invoice_id, period FROM invoice_record")
    conn.execute("INSERT INTO invoice_status SELECT invoice_id, status FROM invoice_record")
    conn.execute("DROP TABLE invoice_record")
    conn.commit()
    conn.close()
    contracts = _load_base_contracts(src)
    contracts.pop("invoice_record", None)
    for table, role, typ in (
        ("invoice_billed", "billed_name", "TEXT"),
        ("invoice_amount", "amount", "REAL"),
        ("invoice_currency", "currency", "TEXT"),
        ("invoice_period", "period", "TEXT"),
        ("invoice_status", "status", "TEXT"),
    ):
        contracts[table] = {
            "physical_table": table,
            "physical_roles": [
                {"role_name": "invoice", "role_type": "REFERENT", "column_name": "invoice"},
                {"role_name": role, "role_type": typ, "column_name": role if role != "billed_name" else "billed_name"},
            ],
            "derivation": "vertical_partition_of_invoice_record",
            "scope": "WORLD",
        }
        if table == "invoice_billed":
            contracts[table]["physical_roles"][1]["column_name"] = "billed_name"
        elif table == "invoice_amount":
            contracts[table]["physical_roles"][1]["column_name"] = "amount"
        else:
            contracts[table]["physical_roles"][1]["column_name"] = role
    (dest.parent / "derivation_contract.json").write_text(
        json.dumps(
            {
                "canonical": "invoice_record",
                "join_role": "invoice",
                "parts": ["invoice_billed", "invoice_amount", "invoice_currency", "invoice_period", "invoice_status"],
            },
            indent=2,
        )
        + "\n"
    )
    _attach(dest, contracts)


def add_noise(src: Path, dest: Path) -> None:
    _copy_world(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("CREATE TABLE name_overlap (left TEXT, right TEXT, disposition TEXT)")
    conn.execute(
        "INSERT INTO name_overlap (left, right, disposition) VALUES (?, ?, ?)",
        ("billing:Helion Robotics Limited", "registry:11847299", "MATCH"),
    )
    conn.commit()
    conn.close()
    contracts = _load_base_contracts(src)
    contracts["name_overlap"] = {
        "physical_table": "name_overlap",
        "physical_roles": [
            {"role_name": "left", "role_type": "TEXT", "column_name": "left"},
            {"role_name": "right", "role_type": "TEXT", "column_name": "right"},
            {"role_name": "disposition", "role_type": "TEXT", "column_name": "disposition"},
        ],
        "dispositions": ["MATCH", "NO_MATCH"],
        "meaning": "Surface name overlap, not legal identity.",
        "scope": "WORLD",
    }
    _attach(dest, contracts)


def generate_all(certified_world: Path) -> dict[str, Path]:
    METAMORPHIC.mkdir(parents=True, exist_ok=True)
    out = {}
    mapping = {
        "b1_rename": METAMORPHIC / "b1_rename" / "world.sqlite",
        "b2_role_rename": METAMORPHIC / "b2_role_rename" / "world.sqlite",
        "b3_orientation": METAMORPHIC / "b3_orientation" / "world.sqlite",
        "b4_physical": METAMORPHIC / "b4_physical" / "world.sqlite",
        "b5_epistemic": METAMORPHIC / "b5_epistemic" / "world.sqlite",
        "b6_decompose": METAMORPHIC / "b6_decompose" / "world.sqlite",
        "b7_noise": METAMORPHIC / "b7_noise" / "world.sqlite",
    }
    rename_tables(certified_world, mapping["b1_rename"], "b1")
    rename_roles(certified_world, mapping["b2_role_rename"], "b2")
    swap_orientation(src=certified_world, dest=mapping["b3_orientation"])
    physical_layout(src=certified_world, dest=mapping["b4_physical"])
    epistemic_split(src=certified_world, dest=mapping["b5_epistemic"])
    decompose_invoices(src=certified_world, dest=mapping["b6_decompose"])
    add_noise(src=certified_world, dest=mapping["b7_noise"])
    return mapping
