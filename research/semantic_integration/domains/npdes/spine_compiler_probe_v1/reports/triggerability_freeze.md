# Triggerability freeze (evaluator-only)

Frozen **before any host-agent model call**. Not shown to participant agents.

Labels: **MEASURED** (from participant structured files + source_manifest filenames), **OBSERVED** (classification).

Primary E1 scoring uses only `STRUCTURE_TRIGGERABLE` and `SOURCE_METADATA_TRIGGERABLE` (7 of 12 GOLD-S seams). `PROSE_ORIGINATING` failures are not primary misses.

| gold_id | class | why |
|---|---|---|
| S-FARM-TDS-STAGE | STRUCTURE_TRIGGERABLE | 70295 dated numeric split 497/27664 then 449/24992; FY2025 straddles |
| S-FARM-CN-SCHEDULE | PROSE_ORIGINATING | single cyanide interval already covers FY2025; 12-month delay not in CSV |
| S-FARM-TRC-CONDITIONAL | PROSE_ORIGINATING | TRC is numeric OPTIONAL=N; chlorine/UV condition is footnote prose |
| S-FARM-REPORT-ONLY | STRUCTURE_TRIGGERABLE | empty LIMIT_VALUE_NMBR beside numeric siblings |
| S-AZTEC-WHEN-DISCHARGING | STRUCTURE_TRIGGERABLE | DMR_COMMENT_TEXT `WHEN DISCHARGING.` |
| S-AZTEC-REPORT-ONLY | STRUCTURE_TRIGGERABLE | empty cyanide/TDS/flow values vs numeric TSS/TRC/pH |
| S-AZTEC-WET-SEASONAL | PROSE_ORIGINATING | no Aztec WET seasonal rows in CSV |
| S-AZTEC-DELTA-BHC | PROSE_ORIGINATING | no BHC parameter in CSV |
| S-GCC-EVENT-DISCHARGE | STRUCTURE_TRIGGERABLE | storm-runoff limit-set name + NODI C mixed with numeric rows |
| S-GCC-REPORT-ONLY | STRUCTURE_TRIGGERABLE | empty vs numeric mixed (TSS daily max 50 vs Report cells) |
| S-GCC-WET-FIRST-DISCHARGE | PROSE_ORIGINATING | no first-discharge WET rows in CSV |
| S-SOURCE-AUTHORITY | SOURCE_METADATA_TRIGGERABLE | permit vs fact-sheet/SOB filenames in inventory; no prose |

No `AMBIGUOUS` classifications.

NODI 9/C legends are **not** in the participant corpus. Generic `UNINTERPRETED_REQUIRED_CODE` on NODI is allowed; inventing NODI meanings is not required for a trigger.
