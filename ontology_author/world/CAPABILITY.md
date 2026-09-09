# Ontology Author capability

Ontology Author enables coding agents to construct and maintain purpose-fit
ontologies called Worlds from the evidence in the current workspace.

A World is a purpose-relative semantic abstraction, not a universal model of
the workspace. Purpose determines which distinctions must survive; it does not
prescribe schema, relation names, or one correct conceptualization. Different
Worlds over the same evidence may make different valid conceptual carvings.
Shared evidence does not imply World-level conceptual identity. Do not merge,
broaden, or reconcile Worlds merely because their grounding overlaps. If a
needed distinction is missing inside the same purpose, revise construction and
rebuild. Capable intelligence belongs in this conversation; the kernel
constrains durable output.

A World is a sealed, read-only semantic artifact: named typed relations,
referents, grounding, derivations, purpose-relative unresolvedness, origins,
and revisions. Conversation is the construction control plane. Work with the
user to understand purpose, inspect project evidence, author or maintain
construction, test queries, and rebuild as meaning or evidence changes.

Use ordinary filesystem, shell, Python, and SQLite access. Do not add MCP or a
model launcher. Do not patch `world/world.sqlite`. Use the installed commands:

```text
author create <world-name>            # initialize .worlds/<name>/
author rebuild <world-name>           # construct, validate, and replace world/
author open <world-name>              # inspect the sealed World locally
author list                           # discover project-local Worlds
```

`author create <name>` creates the World workspace but does not currently
generate `construction.py`. Write that file before `author rebuild`.

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

## Construction contract

`.worlds/<name>/construction.py` is the runtime entrypoint. It must define:

```python
def construct(source, world, purpose):
    ...
```

The runtime supplies `source`, `world`, and `purpose`. It also injects the
stable authoring vocabulary into the construction namespace, so construction
need not import these names from Ontology Author internals:

```text
Role  RoleType  RelationMode  ConstructionOrigin
AssertionGrounding  SourceObservation
Completeness  CompletenessStatus
```

`RoleType` is `REFERENT`, `TEXT`, `INTEGER`, `REAL`, or `BOOLEAN`.
`RelationMode` is `BASE` or `DERIVED`. `ConstructionOrigin` is `MECHANICAL`,
`SEMANTIC`, `DERIVED`, or `ADJUDICATED`. Relation scope is `"WORLD"` or
`"PURPOSE"`.

Construction may use arbitrary additional Python, helpers, and files. This
API is the runtime boundary, not a prescribed construction methodology.

### World

```python
world.add_referent(referent_id, label="")
world.declare_relation(name, roles, mode=RelationMode.BASE, description="", scope="WORLD")
world.assert_tuple(relation, values, origin=..., grounding=None)
world.register_derivation(name, sql=..., inputs=[...])
world.rerun(name, completeness=Completeness(...))
```

`roles` are `Role(name, RoleType.*)` values. `assert_tuple` requires
`origin=ConstructionOrigin.*`. Derived relations are declared with
`mode=RelationMode.DERIVED`, then registered and rerun; do not assert them
directly.

### Evidence

`source` reads the ordinary project tree. Useful operations include:

```python
source.rows(table)
source.read_text(path)
source.fields(table)
source.profile(table, field)
source.distinct_values(table, field)
source.join(left, right, on)
source.grounding(table, location)
```

`on` is a list of `(left_field, right_field)` pairs.

`source.grounding(table, location)` is the usual SOURCE pointer for a WORLD
BASE assertion. `location` is a reconstructible native locator such as a
row key, not copied source content.

### Purpose

```python
purpose.unresolved(name, subject={...}, relation=None, reason="")
```

`purpose.require_*` helpers (`require`, `require_unique`,
`require_materializable`, `require_interpreted`, `require_numeric`) are
optional deterministic purpose checks. They are not a required construction
shape.

## Output rules

WORLD BASE assertions require SOURCE grounding.
PURPOSE-scoped records may be ungrounded.
Derived relations are registered and derived rather than directly asserted.
Mechanical validation is a hard output boundary, not proof that the World is
adequate or true.

## Example

```python
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
    for row in source.rows("accounts.csv"):
        referent = f"account:{row['account_code']}"
        world.add_referent(referent, label=row["legal_name"])
        world.assert_tuple(
            "account",
            {
                "account": referent,
                "account_code": row["account_code"],
                "legal_name": row["legal_name"],
            },
            origin=ConstructionOrigin.MECHANICAL,
            grounding=source.grounding(
                "accounts.csv",
                f"account_code={row['account_code']}",
            ),
        )
    purpose.unresolved(
        "legal_identity",
        relation="account",
        subject={"account": "account:A1"},
        reason="this extract does not establish whether A1 is a legal entity or a trading name",
    )
```

The reusable bundle is `.worlds/<name>/world/` and includes `world.sqlite` plus
its semantic sidecars. Query it directly with SQLite or Python. The bundle is
portable for semantic consumption; project evidence is needed for provenance
verification, and the World construction state plus project evidence is needed
for reconstruction.
