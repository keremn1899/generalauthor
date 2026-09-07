# Evidence-sufficiency audit — Prose Probe v1

Frozen at `2026-09-03T22:54:49.281190+00:00`.

Labels: **MEASURED** corpus presence. Classification is evaluator judgment of whether the GOLD-S semantic distinction can be established from participant sources without extra-corpus legends.

Establishable: **12/12**. Underdetermined: 0. Not present: 0.

Primary scoring uses only `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`.

| gold_id | purposes | source | classification |
|---|---|---|---|
| `S-FARM-TDS-STAGE` | A | `farmington/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-FARM-CN-SCHEDULE` | A, B | `farmington/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-FARM-TRC-CONDITIONAL` | B, C | `farmington/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-FARM-REPORT-ONLY` | A | `farmington/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-AZTEC-WHEN-DISCHARGING` | B, C | `aztec/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-AZTEC-REPORT-ONLY` | A | `aztec/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-AZTEC-WET-SEASONAL` | B, C | `aztec/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-AZTEC-DELTA-BHC` | A, B, C | `aztec/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-GCC-EVENT-DISCHARGE` | B, C | `gcc/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-GCC-REPORT-ONLY` | A | `gcc/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-GCC-WET-FIRST-DISCHARGE` | B, C | `gcc/final_permit.pdf` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |
| `S-SOURCE-AUTHORITY` | A, B, C | `permits vs statement_of_basis/fact_sheet` | `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS` |

## S-FARM-TDS-STAGE

- Affected purposes: A
- Source: `farmington/final_permit.pdf` — Part I, TDS Net Increase table rows and footnotes *10 and *11; cover effective date 2021-12-01
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The final permit states both numeric regimes and their relative intervals. The cover states the effective date, so the *10/*11 calendar split (through 2024-11-30, then from 2024-12-01) is arithmetic over corpus dates. Structured permit_limits.csv independently stores the same date-bounded values (497/27664 ending 11/30/2024; 449/24992 beginning 12/01/2024). FY2025 is declared in Purpose A. Oct–Nov 2024 of FY2025 remain in *10; from Dec 2024 the *11 numbers apply. No extra-corpus legend is required.

## S-FARM-CN-SCHEDULE

- Affected purposes: A, B
- Source: `farmington/final_permit.pdf` — Part I Section B Schedule of Compliance, Cyanide
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The permit states a 12-month cyanide compliance schedule from the effective date. Effective date is on the cover. FY2025 is after 2022-12-01, so final cyanide limits apply. Schedule-completion as an FY2025 excuse is contradicted by the same text.

## S-FARM-TRC-CONDITIONAL

- Affected purposes: B, C
- Source: `farmington/final_permit.pdf` — Part I footnote *5
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Footnote *5 states both UV disinfection and chlorine-use-conditional TRC monitoring. That semantic distinction is in the participant permit. Whether chlorine was actually used in a given FY2025 month is a separate operational fact; DMR NODI code 9 appears on TRC rows but the corpus does not define what '9' means. The obligation that TRC monitoring is event-conditional is establishable; inventing the NODI-9 legend is not.

*Closure note:* Correct bounded judgment for a specific month may be UNRESOLVED if chlorine-use occurrence is not evidenced. That is not a prose-absent failure.

## S-FARM-REPORT-ONLY

- Affected purposes: A
- Source: `farmington/final_permit.pdf` — Part I effluent table Report / N/A cells
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The effluent table literally prints Report versus numeric cells for named parameters.

## S-AZTEC-WHEN-DISCHARGING

- Affected purposes: B, C
- Source: `aztec/final_permit.pdf` — Part I footnote *1
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Footnote *1 attaches When discharging. to marked monitoring frequencies. Intermittent flow is the section heading.

## S-AZTEC-REPORT-ONLY

- Affected purposes: A
- Source: `aztec/final_permit.pdf` — Part I effluent table
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The table prints Report for Flow/Cyanide/TDS and numeric limits for TSS/TRC/pH.

## S-AZTEC-WET-SEASONAL

- Affected purposes: B, C
- Source: `aztec/final_permit.pdf` — Part I footnote *4
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Footnote *4 states once-per-term, first-spring, irrigation-season WET. FY2025 is not automatically a required WET year. Whether the once-per-term test remains outstanding is not established by the permit text alone; gold itself treats that closure as UNRESOLVED unless further evidence exists. The semantic obligation is establishable; forced FY2025 WET-required/not-required closure is not.

*Closure note:* Legitimate P5 output is often UNRESOLVED.

## S-AZTEC-DELTA-BHC

- Affected purposes: A, B, C
- Source: `aztec/final_permit.pdf` — Part I Section B Schedule of Compliance Delta-BHC Study
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The permit states a special-study schedule, not a routine numeric discharge limit. Absence of Delta-BHC on FY2025 DMR limit tables is therefore not by itself a discharge-limit exceedance. The study exists in Part I of the participant permit.

## S-GCC-EVENT-DISCHARGE

- Affected purposes: B, C
- Source: `gcc/final_permit.pdf` — Part I Section A Outfall 001 authorization
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Authorization is event/source-typed rather than continuous municipal discharge. No-discharge reporting is consistent with that authorization. Structured DMR contains NODI C on GCC rows; the corpus does not define code C. The event-dependent authorization itself is in the permit; inventing the NODI-C legend is not required to formulate the obligation, and must not be rewarded as domain knowledge.

## S-GCC-REPORT-ONLY

- Affected purposes: A
- Source: `gcc/final_permit.pdf` — Part I effluent table
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

The table mixes Report and numeric cells, including TSS daily max 50 vs monthly Report.

## S-GCC-WET-FIRST-DISCHARGE

- Affected purposes: B, C
- Source: `gcc/final_permit.pdf` — Part I footnote (2)
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Footnote (2) plus Once/5 years and Report cells establish event-triggered special monitoring, not a monthly numeric DMR limit.

## S-SOURCE-AUTHORITY

- Affected purposes: A, B, C
- Source: `permits vs statement_of_basis/fact_sheet` — permit cover pages vs SOB/fact sheet titles
- Classification: `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`

Each permit cover locates operative effluent limitations in the permit Parts. The accompanying fact sheet/SOB titles themselves as draft-permit basis documents. No extra-corpus hierarchy doctrine is required to notice that Parts I/II are the operative conditions and the fact sheet/SOB is supporting rationale. The corpus does not use the evaluator phrase 'authority hierarchy'.

