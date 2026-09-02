from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixture_db import create_dependencies_db, create_fixture_db


REPOSITORY_ROOT = Path(__file__).resolve().parent.parent


def pytest_collection_modifyitems(items):
    """Skip artifact assertions only when their declared inputs are absent.

    Research result trees are deliberately ignored rather than distributed as
    code fixtures. Tests that audit those results name every required path in a
    ``requires_path`` marker, so they execute in the research checkout and
    report an honest skip in a clean clone.
    """

    for item in items:
        marker = item.get_closest_marker("requires_path")
        if marker is None:
            continue
        required = [REPOSITORY_ROOT / str(path) for path in marker.args]
        missing = [path for path in required if not path.exists()]
        if missing:
            names = ", ".join(
                path.relative_to(REPOSITORY_ROOT).as_posix() for path in missing
            )
            item.add_marker(
                pytest.mark.skip(reason=f"external artifact not present: {names}")
            )


@pytest.fixture
def deps_conn(tmp_path):
    """Ladybug connection with dependencies seed (no API calls)."""
    return create_dependencies_db(tmp_path / "deps_fixture.lbug")


@pytest.fixture
def metabolism_conn(tmp_path):
    """Ladybug connection with metabolism example graph (no API calls)."""
    return create_fixture_db("metabolism", tmp_path / "metabolism_fixture.lbug")


@pytest.fixture
def auth_conn(tmp_path):
    """Ladybug connection with auth_service example graph (no API calls)."""
    return create_fixture_db("auth_service", tmp_path / "auth_fixture.lbug")


@pytest.fixture
def memory_conn(tmp_path):
    """Ladybug connection with memory_cognition example graph (no API calls)."""
    return create_fixture_db("memory_cognition", tmp_path / "memory_fixture.lbug")
