# Ontology Author

Ontology Author lets coding agents construct and maintain purpose-fit
ontologies from the evidence in your workspace.

The resulting ontology is a **World**: grounded, programmable semantic state
available through SQLite, Python, and a local inspector.

## World quickstart

Install the World runtime and its local inspector once:

```bash
uv tool install ontology-author
```

From an existing project, attach the concise World capability to the agent
harness you use:

```bash
author attach cursor
# or: author attach codex
# or: author attach claude
```

Then talk normally to the attached agent, for example:

```text
Build a World for understanding customer support entitlements in this repository.
```

The agent chooses or confirms a World name, creates `.worlds/<name>/`, stores
the purpose and construction program there, and rebuilds as the conversation
develops. The sealed bundle is `.worlds/<name>/world/`.

Useful implementation primitives are:

```bash
author create support-entitlements
author rebuild support-entitlements
author open
```

`open` starts the local read-only API and bundled inspection page. No Node,
npm, Vite, MCP server, or second manually launched backend is required.
SQLite and Python remain direct computation surfaces:

```bash
sqlite3 .worlds/support-entitlements/world/world.sqlite
```

```python
from ontology_author.world import Project

world = Project(".worlds/support-entitlements").open_world()
try:
    rows = world.query_semantic("SELECT * FROM some_relation")
finally:
    world.close()
```

The World bundle is portable for semantic consumption. Project evidence is
kept outside it: the evidence is needed for provenance verification and the
World's construction directory plus evidence are needed for reconstruction.

See [`docs/AGENT_CLIENTS.md`](docs/AGENT_CLIENTS.md) for native attachment
details.

## Legacy graph product

The older Ladybug graph/workbook/MCP product remains in the repository for
compatibility and historical work. Its explicit entrypoints are
`graphauthor-graph`, `graphauthor-mcp`, `graphauthor-workbook`, and the
`mcp_server/`, `source_pipeline/`, and graph frontend surfaces. It is not the
default World workflow.

### Legacy graph traversal

Retrieval does not call a model. Exact lookup stays exact. Search returns
candidates; it does not prove absence.

Named traversals are versioned programs for recurring jobs. Ephemeral
traversals are one-off programs. Every run returns a receipt bound to a graph
version.

```json
{
  "steps": [
    {
      "op": "lookup",
      "references": ["topic:named-traversal"],
      "assign": "seed"
    },
    {
      "op": "expand",
      "from": "$seed",
      "predicates": ["about"],
      "direction": "both",
      "depth": 1,
      "assign": "related"
    }
  ],
  "collect": "$seed + $related",
  "answers": ["related"],
  "limits": {"max_steps": 4, "max_hops": 2, "max_nodes": 20}
}
```

For legacy graph installation and setup, see [the Cursor guide](docs/CURSOR_GUIDE.md).
Point `SST_DB_PATH` at a materialized
`graph.lbug`, and have the agent call `orient` first.

```bash
SST_DB_PATH=/absolute/path/to/graph.lbug graphauthor-mcp
python scripts/run_local_product.py
```

One process owns one graph file at a time.

## Authority

- The agent interprets sources and authors construction and traversal programs.
- The host pins source identity, validates output, runs bounded graph
  operations, and records receipts.
- Durable writes go through `propose`, which auto-commits. Revert is the
  backward path.
- Parsers, segmenters, and workbook programs cannot write the graph.

## Layout

| Path | Role |
|---|---|
| `source_pipeline/` | parsers, workbook, mechanical boundaries |
| `scripts/workbook.py` | prepare, validate, materialize |
| `mcp_server/` | retrieval, traversal, propose, receipts |
| `frontend/` | Graph and Logs |
| `product/` | product contract |
