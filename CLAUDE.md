# Ontology Author contributor guidance

Ontology Author is the current product in this repository. It lets coding
agents construct and maintain purpose-fit ontologies called Worlds from the
evidence in a project workspace.

The public roots are:

- `ontology_author/`: the installed CLI, World runtime, read-only explorer API,
  and bundled inspector assets.
- `ontology_author/world/core/`: the World semantic and SQLite implementation.
- `frontend/`: source for the production World inspector.
- `tests/`: tests for the current product.

The public lifecycle is conversational construction followed by deterministic
runtime primitives:

```text
PURPOSE.md + construction.py
    → temporary candidate
    → validation
    → sealed .worlds/<name>/world/
```

Do not mutate a sealed World directly. Use ordinary filesystem, shell, Python,
and SQLite access. Semantic interpretation and resolution belong in the coding
agent conversation; the inspector is read-only.

Run the current product with:

```bash
uv sync --extra dev
uv run author --help
uv run pytest
```

Build the frontend before building a release wheel. The frontend production
build is copied into `ontology_author/world/static/` and is the only inspector
served by `author open`.

Current product constraints: `docs/FOUNDATIONS.md`.
Research hypotheses and staged experiments: `docs/RESEARCH_DIRECTION.md`.
The research note is not product specification.

Research and historical material is preserved outside the public tree. Do not
reintroduce graph, workbook, MCP, model-provider, or experiment dependencies
into the installed product without an explicit product decision.
