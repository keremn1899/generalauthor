# Experiment freeze

Frozen **before any host-agent model call**.

## Triggerability

Reused **unchanged** from Spine Compiler Probe v1 `frozen/triggerability.json`.

Primary E1 = `STRUCTURE_TRIGGERABLE` + `SOURCE_METADATA_TRIGGERABLE` (7 seams). `PROSE_ORIGINATING` is not a primary miss.

Do not show this file to participant agents.

## What changed vs Spine Compiler Probe v1

The JSON Construction IR is not used. The agent authors `construction.py` against a research World API and structural `Source` helpers. Purposes A/B/C are the primary input.

## What did not change

- Participant structured CSVs and document inventory metadata
- Purposes A/B/C text
- Semantic calculus
- Composer 2.5 + bwrap isolation
- No permit prose, no GOLD, no Purpose D, no constructor/prose-probe/spine-v1 scores in the workspace
