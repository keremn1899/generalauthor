Held-out purpose D, WORLD-ONLY condition.

The environment contains a frozen compiled World, purpose D, and a Python/SQL interface.
Raw source evidence is physically absent. Do not mutate world/world.sqlite.

Read purposes/visible_d.md. Compute purpose_ir/d/output.json from World using Python/SQL.

If World is insufficient, write purpose_ir/d/output.json with
{"purpose": "traceable_result_with_dataset", "insufficient_world": true, "reason": "...", "cases": []}
and do not invent source facts.

Do not read files outside this workspace.
