# Discovery results (E1 orientation, before tasks)

Scored from `NOTES.md` plus orientation traces. Auto-cues in `discovery_targets.json` are a first pass; **behavioral** scores below override cue false positives (notably makerspace member name `Laser A` matching a “misinterpret identity” cue even when notes distinguish member vs tool).

## MEASURED

Auto-cue tallies (9 E1 episodes × 8 targets = 72):

| status | auto count |
| --- | --- |
| DISCOVERED | 61 |
| PARTIAL | 1 |
| NOT_DISCOVERED | 2 |
| MISINTERPRETED | 4 |

Behavioral override (evaluator reading of notes):

| domain | D1 WORLD | D2 PURPOSE | D3 grain | D4 unresolved | D5 path | D6 multi-hop | D7 BASE/DERIVED | D8 grounding |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| harbor ×3 | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED |
| seed ×3 | DISCOVERED | DISCOVERED | DISCOVERED / PARTIAL | DISCOVERED | DISCOVERED | DISCOVERED | mixed* | DISCOVERED |
| makerspace ×3 | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED | DISCOVERED / mixed* | DISCOVERED |

\*D7 is easy to miss in notes even when every relation is BASE; one seed and one makerspace note did not mention BASE/DERIVED. Not a wrong ontology.

Makerspace D6 auto=MISINTERPRETED is **not** behavioral misinterpretation: notes list member `Laser A` separately from tool `LASER-A` and record `L1 → tool:LASER-A`.

## OBSERVED

Without knowing the six tasks, E1 agents found:

- WORLD vs PURPOSE split;
- unresolved failures (B12 emergency, blank hours, status S/H, PENDING);
- join paths (job–vessel–berth; award–org–disbursement; checkout–member–tool + remap);
- SOURCE grounding on WORLD vs ADJUDICATED PURPOSE.

Harbor notes even restated READ RULES. Those same episodes still answered T4=3 and T5=`false` after tasks were revealed. Discovery of structure is not the same as applying grain/epistemic rules under a question.

## HYPOTHESIS

Purpose-relevant structure is discoverable from the compact header plus selective row reads. The remaining product problem is not “agents cannot find the map.”
