"""Public World package surface tests."""

from __future__ import annotations

import json
import sqlite3
import shutil
from pathlib import Path

from ontology_author.world.cli import attach
from ontology_author.world import Project
from ontology_author.world.runtime.entry import create, rebuild
from ontology_author.world.server import build_app
from ontology_author.world.workspaces import WorldSelectionError, discover, select

FIXTURE = Path("research/semantic_integration/runtime_v0/fixtures/minimal_v0")


def _world(tmp_path: Path, name: str) -> Path:
    workspace = tmp_path / ".worlds" / name
    workspace.mkdir(parents=True)
    shutil.copy2(FIXTURE / "construction.py", workspace / "construction.py")
    for filename in ("accounts.csv", "orders.csv", "note.txt"):
        destination = tmp_path / filename
        if not destination.exists():
            shutil.copy2(FIXTURE / "sources" / filename, destination)
    (workspace / "PURPOSE.md").write_text(
        "# Purpose\n\nDetermine customer order amounts.\n\n"
        "## User basis\n\n> Determine customer order amounts.\n",
        encoding="utf-8",
    )
    return workspace


def test_named_worlds_are_independent_and_read_only(tmp_path):
    alpha = _world(tmp_path, "alpha")
    beta = _world(tmp_path, "beta")
    assert rebuild(alpha).succeeded
    assert rebuild(beta).succeeded
    before = (beta / "world" / "world.sqlite").read_bytes()

    assert rebuild(alpha).succeeded
    assert (beta / "world" / "world.sqlite").read_bytes() == before
    assert [item.name for item in discover(tmp_path)] == ["alpha", "beta"]

    world = Project(alpha).open_world()
    try:
        try:
            world.add_referent("account:mutated")
        except ValueError as error:
            assert "read-only" in str(error)
        else:
            raise AssertionError("World accepted a mutation")
    finally:
        world.close()
    try:
        with sqlite3.connect(alpha / "world" / "world.sqlite") as connection:
            connection.execute("CREATE TABLE should_not_exist(value TEXT)")
    except sqlite3.OperationalError:
        pass
    else:
        raise AssertionError("World SQLite file is writable")


def test_selection_is_explicit_when_multiple_worlds_exist(tmp_path):
    for name in ("alpha", "beta"):
        workspace = _world(tmp_path, name)
        assert rebuild(workspace).succeeded
    try:
        select(tmp_path)
    except WorldSelectionError as error:
        assert "alpha" in str(error) and "beta" in str(error)
    else:
        raise AssertionError("ambiguous World selection was accepted")


def test_attach_preserves_existing_harness_configuration(tmp_path):
    cursor_config = tmp_path / ".cursor" / "mcp.json"
    cursor_config.parent.mkdir()
    original = {"mcpServers": {"other": {"command": "keep"}}}
    cursor_config.write_text(json.dumps(original) + "\n", encoding="utf-8")
    result = attach(tmp_path, ["all"])
    assert result["attached"] == ["cursor", "claude", "codex"]
    assert json.loads(cursor_config.read_text(encoding="utf-8")) == original
    assert (tmp_path / ".cursor/rules/ontology-author.mdc").exists()
    assert (tmp_path / ".codex/skills/ontology-author/SKILL.md").exists()
    assert (tmp_path / ".claude/skills/ontology-author/SKILL.md").exists()
    assert "Ontology Author" in (tmp_path / ".cursor/rules/ontology-author.mdc").read_text()
    assert "graphauthor" not in (tmp_path / ".codex/skills/ontology-author/SKILL.md").read_text()


def test_bundled_inspector_is_read_only(tmp_path):
    workspace = _world(tmp_path, "inspector")
    assert rebuild(workspace).succeeded
    from starlette.testclient import TestClient

    with TestClient(build_app(workspace / "world" / "world.sqlite")) as client:
        page = client.get("/")
        assert page.status_code == 200
        assert "ONTOLOGY AUTHOR" in page.text
        assert client.get("/world/overview").json()["world_id"] == "v0"
        assert client.post("/world/judgment", json={}).status_code == 404
        assert client.post(
            "/world/query", json={"sql": "select count(*) from account"}
        ).status_code == 200


def test_create_does_not_generate_per_world_contract_or_sources(tmp_path):
    workspace = tmp_path / ".worlds" / "notes"
    create(workspace)
    assert workspace.is_dir()
    assert not (workspace / "CONSTRUCT.md").exists()
    assert not (workspace / "sources").exists()


def test_purpose_markdown_preserves_exact_user_basis(tmp_path):
    workspace = tmp_path / ".worlds" / "purpose"
    create(workspace)
    purpose = (
        "# Purpose\n\n"
        "Determine the support entitlement for each customer.\n\n"
        "## User basis\n\n"
        "> I want to understand which customers are entitled to what support.\n"
    )
    (workspace / "PURPOSE.md").write_text(purpose, encoding="utf-8")
    assert (workspace / "PURPOSE.md").read_text(encoding="utf-8") == purpose


def test_failed_rebuild_leaves_world_byte_stable(tmp_path):
    workspace = _world(tmp_path, "stable")
    assert rebuild(workspace).succeeded
    before = (workspace / "world" / "world.sqlite").read_bytes()
    (workspace / "construction.py").write_text(
        "def construct(source, world, purpose):\n    raise RuntimeError('no')\n",
        encoding="utf-8",
    )
    result = rebuild(workspace)
    assert not result.succeeded
    assert (workspace / "world" / "world.sqlite").read_bytes() == before
