"""Deterministic spike-1 tests for runtime_v0. No LLM."""

from __future__ import annotations

import shutil
from pathlib import Path

from research.semantic_integration.core.origins import ConstructionOrigin
from research.semantic_integration.runtime_v0.commit import fingerprint_accepted
from research.semantic_integration.runtime_v0.project import Project
from research.semantic_integration.runtime_v0.purpose import FAILURE_RELATION
from research.semantic_integration.runtime_v0.world import ConstructionWorld, GroundingError
from taskview import Role, RoleType

FIXTURE = Path(
    "research/semantic_integration/runtime_v0/fixtures/minimal_v0"
)

UNGROUNDED_CONSTRUCTION = '''
def construct(source, world, purpose):
    world.declare_relation(
        "account",
        [
            Role("account", RoleType.REFERENT),
            Role("account_code", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.add_referent("account:A1", label="Acme Ltd")
    world.assert_tuple(
        "account",
        {
            "account": "account:A1",
            "account_code": "A1",
            "legal_name": "Acme Ltd",
        },
        origin=ConstructionOrigin.SEMANTIC,
        grounding=None,
    )
'''

PARTIAL_THEN_FAIL = '''
def construct(source, world, purpose):
    world.declare_relation(
        "account",
        [
            Role("account", RoleType.REFERENT),
            Role("account_code", RoleType.TEXT),
            Role("legal_name", RoleType.TEXT),
        ],
        scope="WORLD",
    )
    world.add_referent("account:A1", label="Acme Ltd")
    world.assert_tuple(
        "account",
        {
            "account": "account:A1",
            "account_code": "A1",
            "legal_name": "Acme Ltd",
        },
        origin=ConstructionOrigin.MECHANICAL,
        grounding=source.grounding("accounts.csv", "account_code=A1"),
    )
    raise RuntimeError("intentional failure after valid assertions")
'''


def _project(tmp_path: Path) -> Project:
    dest = tmp_path / "minimal_v0"
    shutil.copytree(FIXTURE, dest)
    return Project(dest)


def test_valid_candidate_is_accepted(tmp_path):
    project = _project(tmp_path)
    result = project.run()
    assert result.accepted is True
    assert project.accepted_world.exists()
    assert (project.accepted_dir / "world.sqlite.origins.json").exists()
    assert (project.accepted_dir / "world.purpose.json").exists()
    assert (project.accepted_dir / "world.admission.json").exists()

    world = project.open_accepted()
    try:
        accounts = world.query_semantic("SELECT account_code, legal_name FROM account")
        assert {row["account_code"]: row["legal_name"] for row in accounts} == {
            "A1": "Acme Ltd",
            "A2": "Beta Ltd",
        }
        grounds = world.taskview.query(
            "SELECT kind FROM _tv_groundings WHERE subject_type = 'ASSERTION' AND kind = 'SOURCE'"
        )
        assert grounds
        admission = world.admission
        assert admission["account"] == "WORLD"
        assert admission["customer_order"] == "WORLD"
        assert admission["analysis_policy"] == "PURPOSE"
        assert admission[FAILURE_RELATION] == "PURPOSE"
    finally:
        world.close()


def test_sql_without_reopening_csv_sources(tmp_path):
    project = _project(tmp_path)
    assert project.run().accepted is True
    (project.sources_dir / "orders.csv").unlink()
    (project.sources_dir / "accounts.csv").unlink()

    world = project.open_accepted()
    try:
        rows = world.query_semantic(
            """
            SELECT a.legal_name, o.amount_text
            FROM customer_order AS o
            JOIN account AS a ON a.account_id = o.account_id
            ORDER BY o.amount_text
            """
        )
        by_name = {row["legal_name"]: row["amount_text"] for row in rows}
        assert by_name["Acme Ltd"] == "100"
        assert by_name["Beta Ltd"] == "GM"
    finally:
        world.close()


def test_purpose_failures_are_sql_queryable(tmp_path):
    project = _project(tmp_path)
    assert project.run().accepted is True
    world = project.open_accepted()
    try:
        grouped = world.query_semantic(
            """
            SELECT requirement_id, failure_kind, COUNT(*) AS n
            FROM purpose_requirement_failure
            GROUP BY requirement_id, failure_kind
            """
        )
        kinds = {(row["requirement_id"], row["failure_kind"]): row["n"] for row in grouped}
        assert kinds[("order_amount_numeric", "NOT_NUMERIC")] == 1
        assert kinds[("gm_token", "EXPLICIT_UNRESOLVED")] == 1
        established = world.query_semantic(
            "SELECT amount_text FROM customer_order WHERE amount_text = 'GM'"
        )
        assert len(established) == 1
        # The GM token remains an uninterpreted WORLD amount_text, not a decoded number.
        numeric_facts = world.query_semantic(
            "SELECT statement FROM analysis_policy"
        )
        assert numeric_facts
    finally:
        world.close()


def test_ungrounded_world_base_is_rejected_and_raises(tmp_path):
    project = _project(tmp_path)
    world = ConstructionWorld.create(tmp_path / "direct.sqlite", world_id="v0")
    try:
        world.declare_relation(
            "account",
            [
                Role("account", RoleType.REFERENT),
                Role("account_code", RoleType.TEXT),
                Role("legal_name", RoleType.TEXT),
            ],
            scope="WORLD",
        )
        world.add_referent("account:A1")
        try:
            world.assert_tuple(
                "account",
                {
                    "account": "account:A1",
                    "account_code": "A1",
                    "legal_name": "Acme Ltd",
                },
                origin=ConstructionOrigin.SEMANTIC,
                grounding=None,
            )
            raised = False
        except GroundingError:
            raised = True
        assert raised is True
    finally:
        world.close()

    (project.root / "construction.py").write_text(UNGROUNDED_CONSTRUCTION, encoding="utf-8")
    result = project.run()
    assert result.accepted is False
    assert result.reason == "ungrounded_world_base"
    assert not project.accepted_world.exists()


def test_rejected_candidate_leaves_accepted_world_unchanged(tmp_path):
    project = _project(tmp_path)
    assert project.run().accepted is True
    before = fingerprint_accepted(project.accepted_dir)

    (project.root / "construction.py").write_text(UNGROUNDED_CONSTRUCTION, encoding="utf-8")
    result = project.run()
    assert result.accepted is False
    assert result.reason == "ungrounded_world_base"
    after = fingerprint_accepted(project.accepted_dir)
    assert after == before
    assert not project.candidate_dir.exists()


def test_intentional_construction_failure_is_atomic(tmp_path):
    project = _project(tmp_path)
    assert project.run().accepted is True
    before = fingerprint_accepted(project.accepted_dir)

    (project.root / "construction.py").write_text(PARTIAL_THEN_FAIL, encoding="utf-8")
    result = project.run()
    assert result.accepted is False
    assert result.reason == "construction_error"
    after = fingerprint_accepted(project.accepted_dir)
    assert after == before
    world = project.open_accepted()
    try:
        codes = {row["account_code"] for row in world.query_semantic("SELECT account_code FROM account")}
        assert codes == {"A1", "A2"}
    finally:
        world.close()


def test_purpose_unresolved_is_not_an_established_world_fact(tmp_path):
    project = _project(tmp_path)
    assert project.run().accepted is True
    world = project.open_accepted()
    try:
        failures = world.query_semantic(
            "SELECT requirement_id, failure_kind, relation_name FROM purpose_requirement_failure "
            "WHERE failure_kind = 'EXPLICIT_UNRESOLVED'"
        )
        assert len(failures) == 1
        assert failures[0]["requirement_id"] == "gm_token"
        assert world.admission[FAILURE_RELATION] == "PURPOSE"
        gm_world = world.query_semantic(
            "SELECT amount_text FROM customer_order WHERE amount_text = 'GM'"
        )
        assert gm_world[0]["amount_text"] == "GM"
        policy = world.query_semantic("SELECT statement FROM analysis_policy")
        assert policy
        assert world.admission["analysis_policy"] == "PURPOSE"
        grounds = world.taskview.query(
            "SELECT a.relation_name, g.kind FROM _tv_assertions a "
            "JOIN _tv_groundings g ON g.subject_id = a.assertion_id "
            "WHERE a.relation_name = 'analysis_policy'"
        )
        assert grounds
        assert all(row["kind"] != "SOURCE" for row in grounds)
    finally:
        world.close()
