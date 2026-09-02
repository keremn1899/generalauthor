# Research evidence room (constructor)

You are the constructor participant. Compile a semantic World for purposes A, B, and C.

You have sources, three visible purposes, and a frozen World kernel. You do not have a gold ontology, expected outputs, or any other purpose.

Read KERNEL.md and the purpose files before writing code.

Required layout in this workspace:

```text
construction/compilation_spec.md
construction/vocabulary.json
construction/mechanical_compiler/   (your C0/C1 code)
construction/semantic_frontier/
construction/evidence_selector/
construction/derivations/
world/world.sqlite
world/obligations.json
purpose_ir/a/output.json
purpose_ir/b/output.json
purpose_ir/c/output.json
reports/construction_notes.md
```

`vocabulary.json` must list every relation with: name, ordered roles, role types, one-sentence semantics, admission WORLD|PURPOSE, construction class MECHANICAL|SEMANTIC|DERIVED, required_by, grounding contract, construction rule, and if SEMANTIC the unresolved judgment plus allowed dispositions.

Run Python with PYTHONPATH=. so `import taskview` works.
