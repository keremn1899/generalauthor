"""Fail if default v3 runtime depends on experimental strategies."""

from __future__ import annotations

import ast
from pathlib import Path

RUNTIME = Path(__file__).resolve().parent.parent / "runtime"
FORBIDDEN = (
    "constructor_v2.runtime.verifier",
    "semantic_proof_benchmark",
    "schema_normalization_v1",
)


def test_runtime_does_not_import_experiments() -> None:
    hits = []
    for path in RUNTIME.rglob("*.py"):
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            for name in modules:
                if any(token in name for token in FORBIDDEN):
                    hits.append((str(path), name))
    assert hits == [], hits


if __name__ == "__main__":
    test_runtime_does_not_import_experiments()
    print("ok")
