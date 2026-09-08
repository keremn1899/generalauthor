# Ontology Author capability

Ontology Author enables coding agents to construct and maintain purpose-fit
ontologies called Worlds from the evidence in the current workspace.

A World is a sealed, read-only semantic artifact for a project: named typed
relations, referents, grounding, derivations, purpose-relative unresolvedness,
origins, and revisions. Conversation is the construction control plane. Work
with the user to understand purpose, inspect project evidence, author or
maintain construction, test queries, and rebuild as meaning or evidence
changes.

Use ordinary filesystem, shell, Python, and SQLite access. Do not add MCP or a
model launcher. Do not patch `world/world.sqlite`. Use the installed commands:

```text
author create <world-name>            # initialize .worlds/<name>/
author rebuild <world-name>           # construct, validate, and replace world/
author open <world-name>              # inspect the sealed World locally
author list                           # discover project-local Worlds
```

If the user has not named a World, choose a concise human-readable name and
tell the user which one you used. Maintain that World's `PURPOSE.md` from the
conversation. Its normal shape is:

```markdown
# Purpose

<a concise agent-authored synthesis of the current purpose>

## User basis

> <an exact, materially purpose-defining quotation from the user>
```

Quote user wording verbatim. Never fabricate or paraphrase text inside quote
blocks. Preserve only purpose-defining statements and refinements, not the
whole conversation. Plain attribution to the conversation is enough; a
harness message reference is optional and must never be required for use.

Keep `construction.py` and any other host-authored helpers or checks in the
World directory. The ordinary project tree is the evidence environment; do
not copy project evidence into `.worlds/<name>/`. Construction may be
exploratory. Rebuild constructs a temporary candidate, validates it, and
replaces that World's `world/` only on success. A failed rebuild leaves the
existing World unchanged. Semantic interpretation, clarification, and
resolution belong in the conversation and enter a later rebuild.

WORLD BASE assertions need SOURCE grounding. PURPOSE-scoped records may
represent purpose bookkeeping and unresolved requirements. Mechanical
validation is a hard output boundary, not proof that the World is adequate or
true.

The reusable bundle is `.worlds/<name>/world/` and includes `world.sqlite` plus
its semantic sidecars. Query it directly with SQLite or Python. The bundle is
portable for semantic consumption; project evidence is needed for provenance
verification, and the World construction state plus project evidence is needed
for reconstruction.
