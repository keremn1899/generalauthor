# Frozen World construction contract

The semantic calculus is frozen. You may not add a new primitive.

## Primitives

```text
Referent
Named typed n-ary Relation
Derivation
```

Cross-cutting machinery already implemented by the kernel:

```text
grounding
construction origin
revision
stale/current
scope (as ordinary relations if needed)
completeness receipts
explicit unresolved state where you model it as a relation/role value
```

Do not introduce objects with arbitrary intrinsic fields, a property-graph ontology, event objects, claim objects, constraint objects, set objects, or a custom semantic DSL. Those may only appear as patterns over the primitives above.

Ergonomic inconvenience is not a reason to change the kernel.

## World vs Purpose

For each proposed relation, classify WORLD or PURPOSE.

If the current purpose disappeared, would the proposition still have the same meaning and truth conditions? If yes, it is eligible for World IR.

If interpretation depends on the current analytical question, a threshold, a policy, or a requested decision, keep it in Purpose IR unless those dependencies are explicit arguments that make the proposition independently meaningful.

Do not persist `answer_to_purpose_a(...)` as World truth.

## Construction order

C0 source observations and thin referents. Do not globally canonicalize identity.

C1 mechanical compilation: parsing, explicit IDs, exact joins, dates, amounts, deterministic correspondence.

C2 semantic frontier: unresolved judgments demanded by purposes A/B/C. Not missing tuples from a hidden oracle.

C3 bounded resolution: ACCEPT / REJECT / UNRESOLVED with a small evidence packet. Ground every persistent semantic assertion. If the kernel cannot represent a required negative, record the limitation. Do not invent closed-world negation.

C4 derivation: ordinary Python/SQL over compiled relations.

## Minimality

Minimum sufficient reusable semantics. Do not model the whole scientific universe.

## Kernel API

Python package `taskview` is on PYTHONPATH.

```python
from taskview import (
    TaskView, Role, RoleType, RelationMode, Grounding, GroundingKind,
    Completeness, CompletenessStatus,
)

tv = TaskView("world.sqlite", view_id="compiled-world")
tv.add_referent("src:example", label="...", grounding=[Grounding(GroundingKind.SOURCE, "example.csv", "row example")])
tv.declare_relation("named_relation", [Role("left", RoleType.REFERENT), Role("right", RoleType.REFERENT)], mode=RelationMode.BASE, description="one sentence")
tv.assert_tuple("named_relation", {"left": "...", "right": "..."}, grounding=[...])
tv.declare_relation("derived_rel", [...], mode=RelationMode.DERIVED, description="...")
tv.register_derivation("derived_rel", sql="SELECT ...", inputs=["base_rel"])
tv.run_derivation(
    "derived_rel",
    completeness=Completeness(CompletenessStatus.COMPLETE, universe="other_rel"),
)
```

`RoleType` values: REFERENT, TEXT, INTEGER, REAL, BOOLEAN.

Unresolved semantic demand may also be recorded in `obligations.json` as a JSON list of `{relation, values, judgment, evidence}` objects.

Purpose outputs go under `purpose_ir/{a,b,c}/output.json` and must match the schemas in the purpose files.

Downstream World programs must not reread the heterogeneous source files. Put compiled state in `world/world.sqlite`.
