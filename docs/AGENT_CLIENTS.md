# Ontology Author agent attachment

Install the World runtime once:

```bash
uv tool install ontology-author
```

Run the command from the project root you want the agent to work in:

```bash
author attach cursor
author attach codex
author attach claude
```

Attachment is idempotent and only writes the selected native instruction
surface. It does not add MCP, create a server, copy source evidence, or change
existing client configuration entries.

## Cursor

`author attach cursor` writes or refreshes:

```text
.cursor/rules/ontology-author.mdc
```

It is an always-applied project rule. Existing `.cursor/rules` files and MCP
configuration are left alone.

## Claude Code

`author attach claude` writes or refreshes:

```text
.claude/skills/ontology-author/SKILL.md
```

This uses Claude Code's project-local skill mechanism. Existing skills and
`.mcp.json` are left alone.

## Codex

`author attach codex` writes:

```text
.codex/skills/ontology-author/SKILL.md
```

and adds a marked, replaceable instruction block to the project root
`AGENTS.md`. The block points Codex at the project-local skill, while
preserving all other `AGENTS.md` content. No Codex MCP registration is made.

## Shared capability

All three adapters are generated from the same concise capability contract:

```text
ontology_author/world/CAPABILITY.md
```

The contract tells the agent what a sealed World is, where named Worlds
live, which grounding invariant is hard, and how to use ordinary filesystem,
shell, Python, and SQLite access. It intentionally leaves the construction
conversation open-ended.
