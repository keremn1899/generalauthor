"""Certified-World and morphism checks for the v3 normalizer. Campaign/test only."""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any

from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.catalog import (
    roles_from_tv,
    table_names,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.normalizer import (
    normalize_world,
)
from research.semantic_integration.domains.diligence.constructor_v3_1_1.runtime.projector import (
    project_normalized,
)
from research.semantic_integration.domains.diligence.evaluator import (
    load_json,
    score_purpose_a,
    score_purpose_b,
    score_purpose_c,
    score_purpose_d,
)
from research.semantic_integration.domains.diligence.pass_localization.certified_world import (
    build_certified_world,
)

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
HIDDEN = ROOT.parent / "hidden"


def _with_identity(roles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for role in roles:
        item = dict(role)
        item["semantic_identity"] = item.get("semantic_identity") or item.get("role_name")
        out.append(item)
    return out


def certified_attached_contracts(world: Path) -> dict[str, Any]:
    conn = sqlite3.connect(str(world))
    conn.row_factory = sqlite3.Row
    roles = roles_from_tv(conn)
    tables = table_names(conn)
    conn.close()
    attached = {}
    for table in tables:
        contract: dict[str, Any] = {
            "physical_table": table,
            "physical_roles": _with_identity(roles.get(table) or []),
            "scope": "WORLD",
        }
        if table == "identity_judgment":
            contract["dispositions"] = ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"]
            contract["algebra"] = {"symmetric": True, "transitive": False}
        if table == "contract_clause_kind":
            contract["dispositions"] = ["PRESENT", "ABSENT", "UNRESOLVED"]
        attached[table] = contract
    return attached


def _copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    shutil.copy2(src, dest)


def _attach(dest: Path, contracts: dict[str, Any]) -> None:
    (dest.parent / "attached_contracts.json").write_text(json.dumps(contracts, indent=2) + "\n")


def morphism_rename(src: Path, dest: Path) -> None:
    _copy(src, dest)
    conn = sqlite3.connect(str(dest))
    mapping = {}
    for table in table_names(conn):
        new = f"rel_{table}"
        mapping[table] = new
        conn.execute(f'ALTER TABLE "{table}" RENAME TO "{new}"')
        try:
            conn.execute("UPDATE _tv_relations SET name=? WHERE name=?", (new, table))
            conn.execute("UPDATE _tv_roles SET relation_name=? WHERE relation_name=?", (new, table))
        except sqlite3.Error:
            pass
    conn.commit()
    roles = roles_from_tv(conn)
    conn.close()
    base = certified_attached_contracts(src)
    contracts = {}
    for old, new in mapping.items():
        contract = dict(base.get(old) or {})
        contract["physical_table"] = new
        contract["physical_roles"] = _with_identity(roles.get(new) or contract.get("physical_roles") or [])
        contracts[new] = contract
    _attach(dest, contracts)


def morphism_role_surface(src: Path, dest: Path) -> None:
    """Surface names change; semantic_identity stays the consumer field."""
    _copy(src, dest)
    base = certified_attached_contracts(src)
    contracts = {}
    for table, contract in base.items():
        contract = dict(contract)
        renamed = []
        for role in contract.get("physical_roles") or []:
            item = dict(role)
            item["semantic_identity"] = item.get("role_name")
            item["surface_role_name"] = f"surf_{item.get('role_name')}"
            renamed.append(item)
        contract["physical_roles"] = renamed
        contracts[table] = contract
    _attach(dest, contracts)


def morphism_orientation(src: Path, dest: Path) -> None:
    _copy(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("ALTER TABLE identity_judgment RENAME COLUMN left TO col_b")
    conn.execute("ALTER TABLE identity_judgment RENAME COLUMN right TO col_a")
    conn.execute("UPDATE _tv_roles SET column_name='col_b' WHERE relation_name='identity_judgment' AND role_name='left'")
    conn.execute("UPDATE _tv_roles SET column_name='col_a' WHERE relation_name='identity_judgment' AND role_name='right'")
    conn.commit()
    roles = roles_from_tv(conn)
    conn.close()
    contracts = certified_attached_contracts(src)
    contracts["identity_judgment"]["physical_roles"] = _with_identity(roles.get("identity_judgment") or [])
    _attach(dest, contracts)


def morphism_layout(src: Path, dest: Path) -> None:
    _copy(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute(
        "CREATE TABLE invoice_record_phys AS SELECT status, period, currency, amount, billed_name, invoice_id FROM invoice_record"
    )
    conn.execute("DROP TABLE invoice_record")
    conn.execute("ALTER TABLE invoice_record_phys RENAME TO invoice_record")
    conn.commit()
    conn.close()
    _attach(dest, certified_attached_contracts(src))


def morphism_epistemic(src: Path, dest: Path) -> None:
    _copy(src, dest)
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
    contracts = certified_attached_contracts(src)
    contracts.pop("identity_judgment", None)
    shared = [
        {"role_name": "left", "role_type": "TEXT", "column_name": "left", "semantic_identity": "left"},
        {"role_name": "right", "role_type": "TEXT", "column_name": "right", "semantic_identity": "right"},
    ]
    for table, disp in (
        ("same_entity", "SAME_ENTITY"),
        ("distinct_entity", "DISTINCT"),
        ("unresolved_entity", "UNRESOLVED"),
    ):
        contracts[table] = {
            "physical_table": table,
            "physical_roles": shared,
            "dispositions": ["SAME_ENTITY", "DISTINCT", "UNRESOLVED"],
            "fixed_disposition": disp,
            "scope": "WORLD",
        }
    _attach(dest, contracts)


def morphism_decompose(src: Path, dest: Path) -> None:
    _copy(src, dest)
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
    contracts = certified_attached_contracts(src)
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
                {"role_name": "invoice", "role_type": "REFERENT", "column_name": "invoice", "semantic_identity": "invoice"},
                {"role_name": role, "role_type": typ, "column_name": role, "semantic_identity": role},
            ],
            "scope": "WORLD",
        }
    _attach(dest, contracts)


def morphism_noise(src: Path, dest: Path) -> None:
    _copy(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("CREATE TABLE name_overlap (left TEXT, right TEXT, disposition TEXT)")
    conn.execute(
        "INSERT INTO name_overlap (left, right, disposition) VALUES (?, ?, ?)",
        ("billing:Helion Robotics Limited", "registry:11847299", "MATCH"),
    )
    conn.commit()
    conn.close()
    contracts = certified_attached_contracts(src)
    contracts["name_overlap"] = {
        "physical_table": "name_overlap",
        "physical_roles": [
            {"role_name": "left", "role_type": "TEXT", "column_name": "left", "semantic_identity": "left"},
            {"role_name": "right", "role_type": "TEXT", "column_name": "right", "semantic_identity": "right"},
            {"role_name": "disposition", "role_type": "TEXT", "column_name": "disposition", "semantic_identity": "disposition"},
        ],
        "dispositions": ["MATCH", "NO_MATCH"],
        "scope": "WORLD",
    }
    _attach(dest, contracts)


def morphism_counterparty_surface(src: Path, dest: Path) -> None:
    """Constructor names the role counterparty; semantic_identity binds to counterparty_text."""
    _copy(src, dest)
    conn = sqlite3.connect(str(dest))
    conn.execute("ALTER TABLE contract_record RENAME COLUMN counterparty_text TO counterparty")
    try:
        conn.execute(
            "UPDATE _tv_roles SET role_name='counterparty', column_name='counterparty' "
            "WHERE relation_name='contract_record' AND role_name='counterparty_text'"
        )
    except sqlite3.Error:
        pass
    conn.commit()
    conn.close()
    contracts = certified_attached_contracts(src)
    contracts["contract_record"]["physical_roles"] = [
        {"role_name": "contract_id", "role_type": "TEXT", "column_name": "contract_id", "semantic_identity": "contract_id"},
        {
            "role_name": "counterparty",
            "role_type": "TEXT",
            "column_name": "counterparty",
            "semantic_identity": "counterparty_text",
        },
    ]
    _attach(dest, contracts)


def _score_payload(payload: dict[str, Any]) -> dict[str, Any]:
    expected_a = load_json(HIDDEN / "expected" / "purpose_a.json")
    expected_b = load_json(HIDDEN / "expected" / "purpose_b.json")
    expected_c = load_json(HIDDEN / "expected" / "purpose_c.json")
    expected_d = load_json(HIDDEN / "expected" / "purpose_d.json")
    a = score_purpose_a(payload["a"], expected_a)
    b = score_purpose_b(payload["b"], expected_b)
    c = score_purpose_c(payload["c"], expected_c)
    d = score_purpose_d(payload["d"], expected_d)
    return {
        "A": a.get("pass"),
        "B": b.get("exact"),
        "C": c.get("pass"),
        "D": d.get("pass"),
        "all_exact": bool(a.get("pass") and b.get("exact") and c.get("pass") and d.get("pass")),
    }


def evaluate_world(world: Path) -> dict[str, Any]:
    normalized = normalize_world(world, vocabulary=None)
    projected = project_normalized(normalized)
    scores = _score_payload(projected)
    return {
        "world_correctness": scores,
        "normalization": {
            "consumer_relations_recovered": normalized.get("consumer_relations_recovered"),
            "missing_mappings": normalized.get("missing_mappings"),
            "false_mappings": normalized.get("false_mappings"),
            "role_binding_failures": normalized.get("role_binding_failures"),
        },
    }


def run_certified_suite() -> dict[str, Any]:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    certified = FIXTURES / "certified" / "world.sqlite"
    build_certified_world(certified)
    _attach(certified, certified_attached_contracts(certified))
    baseline = evaluate_world(certified)
    morphisms = {
        "rename": morphism_rename,
        "role_surface": morphism_role_surface,
        "orientation": morphism_orientation,
        "layout": morphism_layout,
        "epistemic": morphism_epistemic,
        "decompose": morphism_decompose,
        "noise": morphism_noise,
        "counterparty_bind": morphism_counterparty_surface,
    }
    morph_results = {}
    for name, fn in morphisms.items():
        dest = FIXTURES / "morphisms" / name / "world.sqlite"
        fn(certified, dest)
        result = evaluate_world(dest)
        morph_results[name] = {
            **result,
            "behavioral_equivalence_to_certified": result["world_correctness"]["all_exact"]
            == baseline["world_correctness"]["all_exact"]
            and result["world_correctness"]["all_exact"],
        }
    return {"certified": baseline, "morphisms": morph_results}


if __name__ == "__main__":
    print(json.dumps(run_certified_suite(), indent=2, sort_keys=True))
