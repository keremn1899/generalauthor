"""Freeze Phase A audit, semantic cards, passages, and oracle obligations BEFORE model runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from research.semantic_integration.domains.npdes.prose_probe_v1.paths import FROZEN, REPORTS
from research.semantic_integration.domains.npdes.prose_probe_v1.segment import (
    find_span,
    write_segmentation,
)

ESTABLISHABLE = "ESTABLISHABLE_FROM_PARTICIPANT_CORPUS"
UNDERDETERMINED = "UNDERDETERMINED_FROM_PARTICIPANT_CORPUS"
NOT_PRESENT = "NOT_PRESENT_IN_PARTICIPANT_CORPUS"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def evidence_audit() -> list[dict]:
    """All 12 GOLD-S seams. Primary scoring uses ESTABLISHABLE only."""
    return [
        {
            "gold_id": "S-FARM-TDS-STAGE",
            "affected_purposes": ["A"],
            "source_document": "farmington/final_permit.pdf",
            "source_locator": "Part I, TDS Net Increase table rows and footnotes *10 and *11; cover effective date 2021-12-01",
            "required_evidence_spans": [
                "TDS net-increase *10 numeric row 27,664 lbs/day / 497 mg/L",
                "TDS net-increase *11 numeric row 24,992 lbs/day / 449 mg/L",
                "*10: limits begin effective date through 3 years from effective date",
                "*11: limits begin 3 years from effective date through expiration",
                "cover: effective 2021-12-01, expire 2026-11-30",
                "Purpose A FY2025 window 2024-10-01/2025-09-30",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "The final permit states both numeric regimes and their relative intervals. "
                "The cover states the effective date, so the *10/*11 calendar split "
                "(through 2024-11-30, then from 2024-12-01) is arithmetic over corpus dates. "
                "Structured permit_limits.csv independently stores the same date-bounded values "
                "(497/27664 ending 11/30/2024; 449/24992 beginning 12/01/2024). "
                "FY2025 is declared in Purpose A. Oct–Nov 2024 of FY2025 remain in *10; "
                "from Dec 2024 the *11 numbers apply. No extra-corpus legend is required."
            ),
        },
        {
            "gold_id": "S-FARM-CN-SCHEDULE",
            "affected_purposes": ["A", "B"],
            "source_document": "farmington/final_permit.pdf",
            "source_locator": "Part I Section B Schedule of Compliance, Cyanide",
            "required_evidence_spans": [
                "Achieve Final Effluent Limitations 12 months after permit effective date",
                "Cyanide numeric table row",
                "cover effective date 2021-12-01",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "The permit states a 12-month cyanide compliance schedule from the effective date. "
                "Effective date is on the cover. FY2025 is after 2022-12-01, so final cyanide "
                "limits apply. Schedule-completion as an FY2025 excuse is contradicted by the same text."
            ),
        },
        {
            "gold_id": "S-FARM-TRC-CONDITIONAL",
            "affected_purposes": ["B", "C"],
            "source_document": "farmington/final_permit.pdf",
            "source_locator": "Part I footnote *5",
            "required_evidence_spans": [
                "This facility uses Ultraviolet disinfection",
                "TRC shall be monitored any time chlorine is used within the treatment plant",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "Footnote *5 states both UV disinfection and chlorine-use-conditional TRC monitoring. "
                "That semantic distinction is in the participant permit. Whether chlorine was actually "
                "used in a given FY2025 month is a separate operational fact; DMR NODI code 9 appears "
                "on TRC rows but the corpus does not define what '9' means. The obligation that TRC "
                "monitoring is event-conditional is establishable; inventing the NODI-9 legend is not."
            ),
            "closure_note": (
                "Correct bounded judgment for a specific month may be UNRESOLVED if chlorine-use "
                "occurrence is not evidenced. That is not a prose-absent failure."
            ),
        },
        {
            "gold_id": "S-FARM-REPORT-ONLY",
            "affected_purposes": ["A"],
            "source_document": "farmington/final_permit.pdf",
            "source_locator": "Part I effluent table Report / N/A cells",
            "required_evidence_spans": [
                "Flow Report MGD",
                "TDS Discharge Report",
                "TDS Water Plants Intake Report",
                "several toxics Report",
                "WET value Report",
            ],
            "classification": ESTABLISHABLE,
            "reason": "The effluent table literally prints Report versus numeric cells for named parameters.",
        },
        {
            "gold_id": "S-AZTEC-WHEN-DISCHARGING",
            "affected_purposes": ["B", "C"],
            "source_document": "aztec/final_permit.pdf",
            "source_locator": "Part I footnote *1",
            "required_evidence_spans": ["*1 When discharging.", "Outfall 001 Intermittent Flow heading"],
            "classification": ESTABLISHABLE,
            "reason": "Footnote *1 attaches When discharging. to marked monitoring frequencies. Intermittent flow is the section heading.",
        },
        {
            "gold_id": "S-AZTEC-REPORT-ONLY",
            "affected_purposes": ["A"],
            "source_document": "aztec/final_permit.pdf",
            "source_locator": "Part I effluent table",
            "required_evidence_spans": [
                "Flow Report",
                "Cyanide Total Recoverable Report",
                "TDS Report",
                "TSS 20/30 numeric",
                "TRC 11 µg/L numeric",
                "pH 6.6/9.0 numeric",
            ],
            "classification": ESTABLISHABLE,
            "reason": "The table prints Report for Flow/Cyanide/TDS and numeric limits for TSS/TRC/pH.",
        },
        {
            "gold_id": "S-AZTEC-WET-SEASONAL",
            "affected_purposes": ["B", "C"],
            "source_document": "aztec/final_permit.pdf",
            "source_locator": "Part I footnote *4",
            "required_evidence_spans": [
                "Once per permit term",
                "first springtime after the permit effective date",
                "during the irrigation season",
                "effective date January 1, 2022",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "Footnote *4 states once-per-term, first-spring, irrigation-season WET. "
                "FY2025 is not automatically a required WET year. Whether the once-per-term test "
                "remains outstanding is not established by the permit text alone; gold itself treats "
                "that closure as UNRESOLVED unless further evidence exists. The semantic obligation "
                "is establishable; forced FY2025 WET-required/not-required closure is not."
            ),
            "closure_note": "Legitimate P5 output is often UNRESOLVED.",
        },
        {
            "gold_id": "S-AZTEC-DELTA-BHC",
            "affected_purposes": ["A", "B", "C"],
            "source_document": "aztec/final_permit.pdf",
            "source_locator": "Part I Section B Schedule of Compliance Delta-BHC Study",
            "required_evidence_spans": [
                "detailed plan to test for Delta-BHC at the source water intake within six months",
                "collect and analyze samples ... 2nd, 3rd, 4th and 5th year",
                "results attached to DMR reports",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "The permit states a special-study schedule, not a routine numeric discharge limit. "
                "Absence of Delta-BHC on FY2025 DMR limit tables is therefore not by itself a "
                "discharge-limit exceedance. The study exists in Part I of the participant permit."
            ),
        },
        {
            "gold_id": "S-GCC-EVENT-DISCHARGE",
            "affected_purposes": ["B", "C"],
            "source_document": "gcc/final_permit.pdf",
            "source_locator": "Part I Section A Outfall 001 authorization",
            "required_evidence_spans": [
                "authorized to discharge storm runoffs from storage and production areas, once-through cooling water, cleaning water, and Artesian well water from Outfall 001",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "Authorization is event/source-typed rather than continuous municipal discharge. "
                "No-discharge reporting is consistent with that authorization. Structured DMR contains "
                "NODI C on GCC rows; the corpus does not define code C. The event-dependent "
                "authorization itself is in the permit; inventing the NODI-C legend is not required "
                "to formulate the obligation, and must not be rewarded as domain knowledge."
            ),
        },
        {
            "gold_id": "S-GCC-REPORT-ONLY",
            "affected_purposes": ["A"],
            "source_document": "gcc/final_permit.pdf",
            "source_locator": "Part I effluent table",
            "required_evidence_spans": [
                "Flow Report",
                "Dissolved copper Report",
                "Dissolved cadmium Report",
                "Hardness daily max Report",
                "TSS monthly average Report; TSS daily max 50",
                "Total aluminum and total copper numeric",
            ],
            "classification": ESTABLISHABLE,
            "reason": "The table mixes Report and numeric cells, including TSS daily max 50 vs monthly Report.",
        },
        {
            "gold_id": "S-GCC-WET-FIRST-DISCHARGE",
            "affected_purposes": ["B", "C"],
            "source_document": "gcc/final_permit.pdf",
            "source_locator": "Part I footnote (2)",
            "required_evidence_spans": [
                "Perform WET testing at first discharge",
                "Once/5 years",
                "WET value Report",
            ],
            "classification": ESTABLISHABLE,
            "reason": "Footnote (2) plus Once/5 years and Report cells establish event-triggered special monitoring, not a monthly numeric DMR limit.",
        },
        {
            "gold_id": "S-SOURCE-AUTHORITY",
            "affected_purposes": ["A", "B", "C"],
            "source_document": "permits vs statement_of_basis/fact_sheet",
            "source_locator": "permit cover pages vs SOB/fact sheet titles",
            "required_evidence_spans": [
                "Farmington cover: in accordance with this cover page and the effluent limitations, monitoring requirements, and other conditions set forth in Part I, Part II, Part III, and Part IV",
                "Aztec cover: set forth in Part I, Part II, and Part III",
                "GCC cover: set forth in Parts I, II, and III",
                "Farmington document titled FACT SHEET FOR THE DRAFT NPDES PERMIT",
                "Aztec document titled STATEMENT OF BASIS FOR THE DRAFT NPDES PERMIT",
                "GCC document titled FACT SHEET FOR THE DRAFT NPDES PERMIT",
            ],
            "classification": ESTABLISHABLE,
            "reason": (
                "Each permit cover locates operative effluent limitations in the permit Parts. "
                "The accompanying fact sheet/SOB titles themselves as draft-permit basis documents. "
                "No extra-corpus hierarchy doctrine is required to notice that Parts I/II are the "
                "operative conditions and the fact sheet/SOB is supporting rationale. "
                "The corpus does not use the evaluator phrase 'authority hierarchy'."
            ),
        },
    ]


def semantic_cards() -> list[dict]:
    """Evaluator-only. No required relation names."""
    return [
        {
            "gold_id": "S-FARM-TDS-STAGE",
            "affected_purpose": "A",
            "semantic_discriminant": (
                "Different numeric TDS net-increase limit regimes govern different temporal intervals; "
                "the applicable numbers are not a single permit-term constant."
            ),
            "required_arguments": [
                "permit NM0020583",
                "outfall 001",
                "parameter TDS net increase",
                "monitoring period (month within FY2025)",
                "the two staged numeric regimes and their intervals",
            ],
            "success_condition": (
                "The obligation must recognize that different limit regimes can govern different "
                "temporal intervals and must ask which regime applies to the relevant monitoring period."
            ),
            "partial_condition": (
                "Mentions TDS net-increase limits or competing TDS numbers without asking which "
                "time-bounded regime governs the monitoring period."
            ),
            "failure_condition": (
                "Treats TDS as a single untensed limit, asks only generic applicability for all "
                "parameters, or returns NO_RELEVANT_OBLIGATION."
            ),
            "full_markers": {
                "all_groups": [
                    ["tds", "total dissolved", "net increase", "70295"],
                    ["stage", "staged", "*10", "*11", "3 year", "three year", "interval", "regime", "time-bound", "temporal", "which regime", "which interval"],
                ],
                "any": ["24992", "24,992", "27664", "27,664", "449", "497", "time-bound", "temporal", "which regime", "which interval"],
            },
        },
        {
            "gold_id": "S-FARM-CN-SCHEDULE",
            "affected_purpose": "A,B",
            "semantic_discriminant": "A compliance schedule delays final cyanide numeric limits until 12 months after the effective date; after that date the final limits govern.",
            "required_arguments": ["permit NM0020583", "cyanide", "schedule completion date vs FY2025 period"],
            "success_condition": "Ask whether the final cyanide effluent limits apply to the FY2025 monitoring period given the 12-month schedule, or which cyanide regime then applies.",
            "partial_condition": "Mentions cyanide limits without the schedule/final-vs-interim distinction.",
            "failure_condition": "Ignores the schedule or treats cyanide as report-only.",
            "full_markers": {
                "all_groups": [
                    ["cyanide"],
                    ["schedule", "12 month", "twelve month", "final effluent", "after permit effective"],
                ]
            },
        },
        {
            "gold_id": "S-FARM-TRC-CONDITIONAL",
            "affected_purpose": "B,C",
            "semantic_discriminant": "TRC monitoring is required when chlorine is used, not as routine UV-plant effluent monitoring.",
            "required_arguments": ["TRC / residual chlorine", "chlorine-use event", "UV disinfection as facility context"],
            "success_condition": "Ask whether TRC monitoring (or a TRC numeric comparison) is applicable for a period given the chlorine-use condition.",
            "partial_condition": "Mentions TRC or UV without the conditional trigger.",
            "failure_condition": "Treats TRC as unconditionally required monthly monitoring or as irrelevant.",
            "full_markers": {
                "all_groups": [
                    ["trc", "residual chlorine", "chlorine"],
                    ["when", "any time", "conditional", "used", "event"],
                ]
            },
        },
        {
            "gold_id": "S-FARM-REPORT-ONLY",
            "affected_purpose": "A",
            "semantic_discriminant": "Some named Farmington parameters are Report / N/A rather than enforceable numeric effluent limits.",
            "required_arguments": ["parameter identity", "report vs numeric cell"],
            "success_condition": "Ask whether a named parameter is an enforceable numeric limit or report-only monitoring for compliance comparison.",
            "partial_condition": "Mentions Report parameters without asking whether numeric exceedance comparison applies.",
            "failure_condition": "Treats all table rows as numeric limits.",
            "full_markers": {
                "all_groups": [
                    ["report-only", "report only", "report rather than", "not a numeric", "numeric comparison not applicable", "not enforceable numeric"],
                ],
            },
        },
        {
            "gold_id": "S-AZTEC-WHEN-DISCHARGING",
            "affected_purpose": "B,C",
            "semantic_discriminant": "Marked Aztec monitoring frequencies apply when discharging; no-discharge periods do not create missing-monitoring violations.",
            "required_arguments": ["Aztec NM0028762", "discharge occurrence", "monitoring frequency *1"],
            "success_condition": "Ask whether monitoring is applicable for a period because a discharge occurred, rather than assuming continuous monthly obligation.",
            "partial_condition": "Mentions intermittent flow without the when-discharging trigger.",
            "failure_condition": "Treats every month as required monitoring regardless of discharge.",
            "full_markers": {
                "all_groups": [
                    ["when discharging", "when-discharging"],
                ]
            },
        },
        {
            "gold_id": "S-AZTEC-REPORT-ONLY",
            "affected_purpose": "A",
            "semantic_discriminant": "Aztec Flow, Cyanide Total Recoverable, and TDS are Report; TSS, TRC, and pH have numeric limits.",
            "required_arguments": ["parameter", "report vs numeric"],
            "success_condition": "Ask whether Cyanide or TDS (or Flow) quarterly Report values are numeric exceedance findings.",
            "partial_condition": "Generic report-only question not tied to Aztec cyanide/TDS/flow.",
            "failure_condition": "Treats cyanide or TDS as numeric effluent limits.",
            "full_markers": {
                "all_groups": [
                    ["report"],
                    ["cyanide", "tds", "total dissolved", "flow"],
                ]
            },
        },
        {
            "gold_id": "S-AZTEC-WET-SEASONAL",
            "affected_purpose": "B,C",
            "semantic_discriminant": "WET is once per permit term during the first springtime after the effective date, during irrigation season — not an automatic FY2025 monthly requirement.",
            "required_arguments": ["WET species", "once-per-term / first spring / irrigation season", "FY2025 vs that window"],
            "success_condition": "Ask whether FY2025 is a required WET monitoring year given the once-per-term first-spring condition, allowing UNRESOLVED if completion evidence is absent.",
            "partial_condition": "Mentions WET without the seasonal/once-per-term restriction.",
            "failure_condition": "Treats WET as routine quarterly/monthly DMR monitoring for FY2025.",
            "full_markers": {
                "all_groups": [
                    ["wet", "ceriodaphnia", "pimephales", "whole effluent"],
                    ["spring", "irrigation", "once per", "once/term", "first spring", "permit term"],
                ]
            },
        },
        {
            "gold_id": "S-AZTEC-DELTA-BHC",
            "affected_purpose": "A,B,C",
            "semantic_discriminant": "Delta-BHC is a special-study / source-water-intake plan obligation, not a routine DMR numeric discharge limit.",
            "required_arguments": ["Delta-BHC", "study/plan vs effluent limit"],
            "success_condition": "Ask whether Delta-BHC is a special-study obligation rather than a FY2025 numeric discharge-limit comparison, or whether DMR absence is a limit exceedance.",
            "partial_condition": "Mentions Delta-BHC without distinguishing study from numeric limit.",
            "failure_condition": "Treats missing Delta-BHC DMR as a discharge-limit exceedance.",
            "full_markers": {
                "all_groups": [
                    ["delta-bhc", "delta bhc", "bhc"],
                    ["study", "special", "source water", "plan", "intake"],
                ]
            },
        },
        {
            "gold_id": "S-GCC-EVENT-DISCHARGE",
            "affected_purpose": "B,C",
            "semantic_discriminant": "Outfall 001 authorization is for specified event/source discharges (storm runoff, once-through cooling, cleaning water, Artesian well water), not continuous discharge.",
            "required_arguments": ["GCC NM0000116", "outfall 001", "discharge occurrence / event type"],
            "success_condition": "Ask whether monitoring or numeric comparison is applicable only when such a discharge occurs.",
            "partial_condition": "Mentions stormwater or cooling water without event-dependence of monitoring.",
            "failure_condition": "Treats GCC as a continuously discharging municipal WWTP for every month.",
            "full_markers": {
                "all_groups": [
                    ["storm runoff", "once-through", "artesian", "when discharging", "event-dependent", "event dependent", "no-discharge", "no discharge"],
                ]
            },
        },
        {
            "gold_id": "S-GCC-REPORT-ONLY",
            "affected_purpose": "A",
            "semantic_discriminant": "GCC mixes Report parameters with numeric limits; TSS daily max 50 is enforceable while TSS monthly average is Report.",
            "required_arguments": ["parameter", "statistical base (monthly vs daily)", "report vs numeric"],
            "success_condition": "Ask which GCC parameters/bases are numeric exceedance comparisons versus Report-only.",
            "partial_condition": "Generic report-only without GCC mixed TSS daily-max vs monthly-report.",
            "failure_condition": "Treats dissolved Cu/Cd or hardness as numeric exceedances, or TSS monthly as a numeric limit.",
            "full_markers": {
                "all_groups": [
                    ["report"],
                    ["dissolved copper", "dissolved cadmium", "hardness", "tss", "suspended", "50"],
                ]
            },
        },
        {
            "gold_id": "S-GCC-WET-FIRST-DISCHARGE",
            "affected_purpose": "B,C",
            "semantic_discriminant": "WET is required at first discharge and at Once/5 years, not as a monthly numeric DMR limit.",
            "required_arguments": ["WET", "first discharge / once per 5 years"],
            "success_condition": "Ask whether monthly missing WET is a numeric exceedance or whether WET is event-triggered special monitoring.",
            "partial_condition": "Mentions GCC WET without first-discharge or once/5-year trigger.",
            "failure_condition": "Treats missing monthly WET as a numeric exceedance.",
            "full_markers": {
                "all_groups": [
                    ["wet", "ceriodaphnia", "pimephales", "whole effluent"],
                    ["first discharge", "once/5", "once per 5", "5 year"],
                ]
            },
        },
        {
            "gold_id": "S-SOURCE-AUTHORITY",
            "affected_purpose": "A,B,C",
            "semantic_discriminant": "Operative effluent limitations and monitoring requirements are set forth in the permit Parts; fact sheets/statements of basis explain draft-permit rationale and are not independent effluent limits.",
            "required_arguments": ["document kind (permit Part vs fact sheet/SOB)", "the condition being applied"],
            "success_condition": (
                "Ask which document class is the operative source of an effluent limitation or monitoring requirement, "
                "or whether a fact-sheet/SOB statement independently establishes a limit."
            ),
            "partial_condition": "Mentions fact sheet or SOB as a source without the operative-vs-rationale distinction.",
            "failure_condition": "Treats fact-sheet/SOB numbers as independent effluent limits, or never asks the hierarchy question.",
            "full_markers": {
                "all_groups": [
                    ["fact sheet", "statement of basis", "sob", "operative", "rationale", "set forth in part", "permit parts", "draft permit", "supporting"],
                ]
            },
        },
    ]


def passages() -> dict:
    """Positive gold passages and negative controls. Frozen before model runs."""
    farm = "farmington/final_permit.txt"
    aztec = "aztec/final_permit.txt"
    gcc = "gcc/final_permit.txt"
    farm_sob = "farmington/statement_of_basis.txt"
    aztec_sob = "aztec/statement_of_basis.txt"
    gcc_fs = "gcc/fact_sheet.txt"

    positives = {
        "S-FARM-TDS-STAGE": {
            "needles": [
                "Total Dissolved Solids, Net     27,664 lbs/day",
                "Total Dissolved Solids, Net     24,992 lbs/day",
                "*10     The limits begin on the effective date of this permit and lasting through 3 years from the permit effective date.",
                "*11     The limits apply during the period beginning 3 year from the permit effective date",
            ],
            "document": farm,
            "heading": "PART I – REQUIREMENTS FOR NPDES PERMITS / FINAL Effluent Limits – Outfall 001",
            "adjacent": "cover effective date December 1, 2021; expiration November 30, 2026",
        },
        "S-FARM-CN-SCHEDULE": {
            "needles": [
                "The permittee shall achieve compliance with the Cyanide effluent limitations specified for",
                "Achieve Final Effluent Limitations 12 months after permit effective date",
            ],
            "document": farm,
            "heading": "SECTION B - SCHEDULE OF COMPLIANCE",
        },
        "S-FARM-TRC-CONDITIONAL": {
            "needles": [
                "*5      This facility uses Ultraviolet disinfection. Total Residual Chlorine (TRC) shall be monitored any time chlorine is used within the treatment plant for",
            ],
            "document": farm,
            "heading": "Part I footnotes",
        },
        "S-FARM-REPORT-ONLY": {
            "needles": [
                "Flow                       Report MGD      Report MGD      Report MGD",
                "Total Dissolved Solids,                                                                                                               12-Hour\n                              Report          Report          N/A          Report        Report        N/A          1/Week",
                "Daphnia pulex                                                Report                Once/Quarter",
            ],
            "document": farm,
            "heading": "FINAL Effluent Limits table",
        },
        "S-AZTEC-WHEN-DISCHARGING": {
            "needles": ["*1 When discharging."],
            "document": aztec,
            "heading": "FINAL Effluent Limits – Outfall 001 – Intermittent Flow / Footnotes",
        },
        "S-AZTEC-REPORT-ONLY": {
            "needles": [
                "Cyanide, Total Recoverable            Report           Report     Report             Report    1/Quarter (*1)",
                "Total Dissolved Solids                Report           Report     Report             Report    1/Quarter (*1)",
            ],
            "document": aztec,
            "heading": "DISCHARGE LIMITATIONS table",
        },
        "S-AZTEC-WET-SEASONAL": {
            "needles": [
                "*4 Once per permit term. The test is to be performed during the first springtime after the permit effective date, during the irrigation season",
            ],
            "document": aztec,
            "heading": "Part I footnotes",
        },
        "S-AZTEC-DELTA-BHC": {
            "needles": [
                "The permittee is required to submit a detailed plan to test for Delta-BHC at the source water",
            ],
            "document": aztec,
            "heading": "B. SCHEDULE OF COMPLIANCE / Delta-BHC Study",
        },
        "S-GCC-EVENT-DISCHARGE": {
            "needles": [
                "discharge storm runoffs from storage and production areas, once-through cooling water, cleaning water, and Artesian well water from",
            ],
            "document": gcc,
            "heading": "PART I SECTION A Outfalls 001",
        },
        "S-GCC-REPORT-ONLY": {
            "needles": [
                "Flow                     Report MGD        Report MGD",
                "Dissolved Copper         N/A               N/A               Report            Report",
                "Total Suspended          N/A               N/A               Report            50",
            ],
            "document": gcc,
            "heading": "Outfall 001 effluent table",
        },
        "S-GCC-WET-FIRST-DISCHARGE": {
            "needles": [
                "(2) Perform WET testing at first discharge.",
                "Ceriodaphnia dubia                     Report            Once/5 years",
            ],
            "document": gcc,
            "heading": "WHOLE EFFLUENT TOXICITY TESTING / Footnote (2)",
        },
        "S-SOURCE-AUTHORITY": {
            "needles": [
                "in accordance with this cover page and the effluent limitations, monitoring requirements, and other\nconditions set forth in Part I, Part II, Part III, and Part IV hereof.",
            ],
            "document": farm,
            "heading": "AUTHORIZATION TO DISCHARGE cover",
            "paired_documents": [
                {"document": farm_sob, "needle": "FACT SHEET\nFOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM"},
                {"document": aztec_sob, "needle": "STATEMENT OF BASIS\nFOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM"},
                {"document": gcc_fs, "needle": "FACT SHEET\nFOR THE DRAFT NATIONAL POLLUTANT DISCHARGE ELIMINATION SYSTEM"},
            ],
        },
    }

    negatives = {
        "S-FARM-TDS-STAGE": [
            {"document": farm, "needle": "City of Farmington\n                      800 Municipal Drive\n                      Farmington, NM 87401-2663", "why_negative": "descriptive facility mailing address; does not change A/B/C limit or monitoring computation"},
            {"document": farm, "needle": "This permit prepared by Quang Nguyen, Environmental Engineer, Permitting Section (6WQ-PE)", "why_negative": "administrative authorship boilerplate"},
        ],
        "S-FARM-CN-SCHEDULE": [
            {"document": farm, "needle": "(This page intentionally left blank)", "why_negative": "blank page; no operative condition"},
            {"document": farm, "needle": "Charles W. Maguire\nDirector\nWater Division (6WQ)", "why_negative": "signature block / administrative boilerplate"},
        ],
        "S-FARM-TRC-CONDITIONAL": [
            {"document": farm, "needle": "This permit supersedes and replaces NPDES Permit No. NM0020583 issued on September 30, 2016.", "why_negative": "historical prior-permit description"},
            {"document": farm, "needle": "Issued on October 21, 2021", "why_negative": "issuance-date administrative boilerplate; not an effluent regime"},
        ],
        "S-FARM-REPORT-ONLY": [
            {"document": farm, "needle": "Outfall 001: Latitude 36° 43' 02\" N, Longitude 108° 13' 15\" W", "why_negative": "descriptive facility coordinates"},
            {"document": farm, "needle": "is authorized to discharge to receiving waters named San Juan River in the San Juan Basin,", "why_negative": "receiving-water identity; does not change Report vs numeric cell semantics"},
        ],
        "S-AZTEC-WHEN-DISCHARGING": [
            {"document": aztec, "needle": "City of Aztec - Water Treatment Plant\n                          201 West Chaco\n                          Aztec, New Mexico 87410", "why_negative": "descriptive facility address"},
            {"document": aztec, "needle": "This Page Intentionally Left Blank", "why_negative": "blank page"},
        ],
        "S-AZTEC-REPORT-ONLY": [
            {"document": aztec, "needle": "Issued on December 2, 2021", "why_negative": "administrative issuance boilerplate"},
            {"document": aztec, "needle": "Charles W. Maguire\n                                                Director\n                                                Water Division (WD)", "why_negative": "signature block"},
        ],
        "S-AZTEC-WET-SEASONAL": [
            {"document": aztec, "needle": "This is a reissue, prepared by Maria Okpala, Environmental Engineer, Permitting Section", "why_negative": "administrative authorship"},
            {"document": aztec, "needle": "There shall be no discharge of floating solids or visible foam in other than trace amounts.", "why_negative": "narrative aesthetics prohibition; not the WET seasonal special-study rule and not an FY2025 numeric DMR parameter in GOLD S"},
        ],
        "S-AZTEC-DELTA-BHC": [
            {"document": aztec, "needle": "violations of daily maximum limitations\nfor the following pollutants shall be reported orally", "why_negative": "24-hour oral reporting procedure with empty pollutant list; not the Delta-BHC study"},
            {"document": aztec, "needle": "Until approved for Net DMR, the permittee shall request temporary or emergency waivers from\nelectronic reporting.", "why_negative": "NetDMR electronic-reporting boilerplate"},
        ],
        "S-GCC-EVENT-DISCHARGE": [
            {"document": gcc, "needle": "GCC Rio Grande, Inc.\n                      P.O. Box 100\n                      Tijeras, NM 87059", "why_negative": "descriptive facility address"},
            {"document": gcc, "needle": "This permit supersedes and replaces NPDES Permit No. NM0000116 issued November 23,\n2010.", "why_negative": "historical prior-permit description"},
        ],
        "S-GCC-REPORT-ONLY": [
            {"document": gcc, "needle": "Issued on May 24, 2021", "why_negative": "administrative issuance boilerplate"},
            {"document": gcc, "needle": "(This Page intentionally left blank)", "why_negative": "blank page"},
        ],
        "S-GCC-WET-FIRST-DISCHARGE": [
            {"document": gcc, "needle": "Director\nWater Division", "why_negative": "signature block"},
            {"document": gcc, "needle": "There shall be no discharge of oils, scum, grease and other floating materials that\nwould cause the formation of a visible sheen", "why_negative": "narrative sheen prohibition; not WET first-discharge monitoring"},
        ],
        "S-SOURCE-AUTHORITY": [
            {"document": farm_sob, "needle": "4Q3   Lowest four-day average flow rate expected to occur once every three-years", "why_negative": "irrelevant abbreviation glossary; not an operative effluent limit"},
            {"document": farm_sob, "needle": "VOICE: 214-665-7238\nFAX: 214-665-2191\nEMAIL: Nguyen.quang@epa.gov", "why_negative": "preparer contact boilerplate"},
        ],
    }

    resolved_pos = {}
    for gid, spec in positives.items():
        spans = [find_span(spec["document"], n) for n in spec["needles"]]
        paired = []
        for extra in spec.get("paired_documents") or []:
            paired.append(find_span(extra["document"], extra["needle"]))
        resolved_pos[gid] = {
            "gold_id": gid,
            "document": spec["document"],
            "heading": spec.get("heading"),
            "adjacent": spec.get("adjacent"),
            "spans": spans,
            "paired_spans": paired,
        }

    resolved_neg = {}
    for gid, items in negatives.items():
        resolved_neg[gid] = []
        for item in items:
            loc = find_span(item["document"], item["needle"])
            loc["why_negative"] = item["why_negative"]
            resolved_neg[gid].append(loc)

    return {"positives": resolved_pos, "negatives": resolved_neg}


def oracle_obligations() -> list[dict]:
    """Evaluator-only oracle questions. Do not include correct dispositions."""
    return [
        {
            "gold_id": "S-FARM-TDS-STAGE",
            "obligation_id": "oracle:S-FARM-TDS-STAGE",
            "relation": "limit_regime_applies",
            "oracle_intervention": True,
            "question": (
                "Which TDS net-increase numeric limit regime governs permit NM0020583 / Outfall 001 / "
                "parameter TDS net increase during each FY2025 monitoring period — the regime that begins "
                "on the effective date and lasts through 3 years from the effective date, or the regime that "
                "begins 3 years from the effective date and lasts through expiration?"
            ),
            "values": {
                "permit": "NM0020583",
                "outfall": "001",
                "parameter": "TDS net increase",
                "period_universe": "FY2025 monthly monitoring periods",
            },
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": (
                "A named numeric limit regime applies to a permit/outfall/parameter during a dated interval. "
                "ACCEPT means the stated regime-interval pairing is established by the packet. "
                "Do not be told which regime is correct for FY2025."
            ),
            "p1_gap_note": (
                "Original trials declare applicable_limit_selection and permit_limit_schedule_row with "
                "begin/end dates, but not a dedicated staged-regime relation. VOCABULARY_GAP relative to "
                "an explicit time-staged regime name; representable via dated limit rows."
            ),
        },
        {
            "gold_id": "S-FARM-CN-SCHEDULE",
            "obligation_id": "oracle:S-FARM-CN-SCHEDULE",
            "relation": "final_limit_schedule_applies",
            "oracle_intervention": True,
            "question": (
                "Do the final Cyanide effluent limitations for NM0020583 Outfall 001 apply during FY2025 "
                "given the Part I schedule to achieve final limitations 12 months after the permit effective date?"
            ),
            "values": {"permit": "NM0020583", "parameter": "Cyanide", "period": "FY2025"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "Final numeric cyanide limits apply in a period if the compliance-schedule completion date has passed.",
        },
        {
            "gold_id": "S-FARM-TRC-CONDITIONAL",
            "obligation_id": "oracle:S-FARM-TRC-CONDITIONAL",
            "relation": "conditional_monitoring_applies",
            "oracle_intervention": True,
            "question": (
                "Is TRC monitoring for NM0020583 required as routine UV-plant effluent monitoring, or only "
                "when chlorine is used in the treatment plant, for FY2025 periods?"
            ),
            "values": {"permit": "NM0020583", "parameter": "TRC"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": (
                "ACCEPT a proposition only if the packet establishes it. If chlorine-use occurrence in a "
                "month is not evidenced, UNRESOLVED is allowed for that month's required/not-required status."
            ),
        },
        {
            "gold_id": "S-FARM-REPORT-ONLY",
            "obligation_id": "oracle:S-FARM-REPORT-ONLY",
            "relation": "numeric_comparison_applicable",
            "oracle_intervention": True,
            "question": (
                "For Farmington Flow, TDS discharge, TDS intake, named Report toxics, and WET, is numeric "
                "effluent-limit exceedance comparison applicable?"
            ),
            "values": {"permit": "NM0020583", "parameters": ["Flow", "TDS discharge", "TDS intake", "WET", "named Report toxics"]},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "ACCEPT means numeric comparison applies; REJECT means it does not (report-only / N/A).",
        },
        {
            "gold_id": "S-AZTEC-WHEN-DISCHARGING",
            "obligation_id": "oracle:S-AZTEC-WHEN-DISCHARGING",
            "relation": "conditional_monitoring_applies",
            "oracle_intervention": True,
            "question": (
                "Do Aztec Outfall 001 monitoring frequencies marked *1 apply in a period only when discharging, "
                "such that no-discharge periods do not by themselves establish missing-required-monitoring?"
            ),
            "values": {"permit": "NM0028762", "outfall": "001"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "ACCEPT the when-discharging condition as the applicability rule if the packet establishes it.",
        },
        {
            "gold_id": "S-AZTEC-REPORT-ONLY",
            "obligation_id": "oracle:S-AZTEC-REPORT-ONLY",
            "relation": "numeric_comparison_applicable",
            "oracle_intervention": True,
            "question": "Are Aztec Flow, Cyanide Total Recoverable, and TDS Report values numeric effluent-limit exceedance findings?",
            "values": {"permit": "NM0028762", "parameters": ["Flow", "Cyanide Total Recoverable", "TDS"]},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "REJECT means numeric exceedance comparison is not applicable (report-only).",
        },
        {
            "gold_id": "S-AZTEC-WET-SEASONAL",
            "obligation_id": "oracle:S-AZTEC-WET-SEASONAL",
            "relation": "special_monitoring_window_applies",
            "oracle_intervention": True,
            "question": (
                "Is FY2025 automatically a required Aztec WET monitoring year, given once-per-term testing "
                "during the first springtime after the effective date during irrigation season?"
            ),
            "values": {"permit": "NM0028762", "parameter": "WET"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": (
                "ACCEPT = FY2025 is established as a required WET year. REJECT = established as not required. "
                "UNRESOLVED if the packet does not establish whether the once-per-term test remains outstanding."
            ),
        },
        {
            "gold_id": "S-AZTEC-DELTA-BHC",
            "obligation_id": "oracle:S-AZTEC-DELTA-BHC",
            "relation": "special_study_not_numeric_limit",
            "oracle_intervention": True,
            "question": (
                "Is the Delta-BHC source-water-intake study a special-study / compliance-schedule obligation "
                "rather than a routine FY2025 DMR numeric discharge limit, such that DMR absence of Delta-BHC "
                "is not by itself a discharge-limit exceedance?"
            ),
            "values": {"permit": "NM0028762", "parameter": "Delta-BHC"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "ACCEPT the special-study characterization if established by the packet.",
        },
        {
            "gold_id": "S-GCC-EVENT-DISCHARGE",
            "obligation_id": "oracle:S-GCC-EVENT-DISCHARGE",
            "relation": "conditional_monitoring_applies",
            "oracle_intervention": True,
            "question": (
                "Is GCC Outfall 001 monitoring required continuously every month, or when the authorized "
                "event-type discharges (storm runoff, once-through cooling, cleaning water, Artesian well water) occur?"
            ),
            "values": {"permit": "NM0000116", "outfall": "001"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "Judge the applicability rule. Do not invent NODI-code legends absent from the packet.",
        },
        {
            "gold_id": "S-GCC-REPORT-ONLY",
            "obligation_id": "oracle:S-GCC-REPORT-ONLY",
            "relation": "numeric_comparison_applicable",
            "oracle_intervention": True,
            "question": (
                "For GCC Outfall 001, which of Flow, dissolved copper, dissolved cadmium, hardness, TSS monthly "
                "average, TSS daily maximum, total aluminum, and total copper are numeric exceedance comparisons "
                "versus Report-only?"
            ),
            "values": {"permit": "NM0000116", "outfall": "001"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "Per-parameter numeric-comparison applicability. Mixed answers may be expressed in rationale with per-parameter REJECT/ACCEPT.",
        },
        {
            "gold_id": "S-GCC-WET-FIRST-DISCHARGE",
            "obligation_id": "oracle:S-GCC-WET-FIRST-DISCHARGE",
            "relation": "event_triggered_monitoring",
            "oracle_intervention": True,
            "question": (
                "Is GCC WET a monthly DMR numeric limit, or event-triggered special monitoring at first discharge "
                "and Once/5 years?"
            ),
            "values": {"permit": "NM0000116", "parameter": "WET"},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "ACCEPT the event-triggered special-monitoring characterization if established.",
        },
        {
            "gold_id": "S-SOURCE-AUTHORITY",
            "obligation_id": "oracle:S-SOURCE-AUTHORITY",
            "relation": "operative_source_class",
            "oracle_intervention": True,
            "question": (
                "Are FY2025 enforceable effluent limitations and monitoring requirements set forth in the permit "
                "Parts, with fact sheets/statements of basis as supporting rationale for the draft permit, rather "
                "than as independent effluent limits?"
            ),
            "values": {"facilities": ["NM0020583", "NM0028762", "NM0000116"]},
            "allowed_dispositions": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "relation_meaning": "ACCEPT the operative-Parts vs rationale-fact-sheet/SOB distinction if the packet establishes it.",
        },
    ]


def expected_b2() -> dict:
    """Evaluator-only expected safe dispositions. Not shown to the model."""
    return {
        "S-FARM-TDS-STAGE": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT that two time-bounded regimes exist and that post-2024-12-01 FY2025 months fall in the later regime",
            "unsupported_closure": "ACCEPT that *10 numbers apply to all of FY2025, or invent numbers absent from the packet",
        },
        "S-FARM-CN-SCHEDULE": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT that final cyanide limits apply in FY2025",
            "unsupported_closure": "REJECT final-limits-apply without contrary packet evidence",
        },
        "S-FARM-TRC-CONDITIONAL": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT the chlorine-use conditional monitoring rule; month-level required/not-required may be UNRESOLVED",
            "unsupported_closure": "ACCEPT that TRC was/was-not required in a month without chlorine-use evidence; invent NODI-9 meaning",
        },
        "S-FARM-REPORT-ONLY": {
            "safe": ["REJECT", "ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "REJECT numeric-comparison-applicable for the named Report parameters",
            "unsupported_closure": "ACCEPT numeric exceedance comparison for Report-only parameters",
        },
        "S-AZTEC-WHEN-DISCHARGING": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT the when-discharging applicability rule",
            "unsupported_closure": "REJECT the rule; or ACCEPT that a specific month had a discharge without evidence",
        },
        "S-AZTEC-REPORT-ONLY": {
            "safe": ["REJECT", "UNRESOLVED"],
            "correct_if_closed": "REJECT numeric exceedance for Flow/Cyanide/TDS Report cells",
            "unsupported_closure": "ACCEPT those Report values as numeric exceedances",
        },
        "S-AZTEC-WET-SEASONAL": {
            "safe": ["UNRESOLVED", "REJECT"],
            "correct_if_closed": "REJECT automatic FY2025 WET-required; UNRESOLVED whether the once-per-term test remains outstanding",
            "unsupported_closure": "ACCEPT that FY2025 WET is required, or ACCEPT that it was completed, without packet evidence",
        },
        "S-AZTEC-DELTA-BHC": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT special-study characterization",
            "unsupported_closure": "REJECT and treat as numeric discharge limit exceedance",
        },
        "S-GCC-EVENT-DISCHARGE": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT event-dependent authorization/monitoring",
            "unsupported_closure": "invent NODI-C meaning; ACCEPT no-discharge as a violation",
        },
        "S-GCC-REPORT-ONLY": {
            "safe": ["ACCEPT", "REJECT", "UNRESOLVED"],
            "correct_if_closed": "mixed: Report parameters REJECT numeric comparison; TSS daily max 50 ACCEPT numeric comparison",
            "unsupported_closure": "ACCEPT numeric comparison for dissolved Cu/Cd/hardness/TSS monthly Report",
        },
        "S-GCC-WET-FIRST-DISCHARGE": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT event-triggered / once-per-5-years special monitoring",
            "unsupported_closure": "ACCEPT missing monthly WET as numeric exceedance",
        },
        "S-SOURCE-AUTHORITY": {
            "safe": ["ACCEPT", "UNRESOLVED"],
            "correct_if_closed": "ACCEPT operative Parts vs rationale fact-sheet/SOB",
            "unsupported_closure": "REJECT and treat fact-sheet numbers as independent effluent limits",
        },
    }


def freeze() -> dict:
    FROZEN.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    audit = evidence_audit()
    cards = semantic_cards()
    pas = passages()
    oracles = oracle_obligations()
    expected = expected_b2()
    seg_path = write_segmentation()
    artifacts = {
        "evidence_sufficiency.json": audit,
        "semantic_cards.json": cards,
        "passages.json": pas,
        "oracle_obligations.json": oracles,
        "expected_b2.json": expected,
    }
    hashes = {}
    for name, payload in artifacts.items():
        path = FROZEN / name
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        hashes[name] = _sha(path)
    hashes["segmentation.json"] = _sha(seg_path)
    hashes["segmentation_pages.json"] = _sha(FROZEN / "segmentation_pages.json")
    meta = {
        "experiment_id": "npdes-prose-probe-v1",
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "n_gold_s": 12,
        "n_establishable": sum(1 for a in audit if a["classification"] == ESTABLISHABLE),
        "n_underdetermined": sum(1 for a in audit if a["classification"] == UNDERDETERMINED),
        "n_not_present": sum(1 for a in audit if a["classification"] == NOT_PRESENT),
        "hashes": hashes,
        "note": "Frozen before new model calls. Evaluator-only gold/cards/oracles are not participant inputs except permitted B1 passages and B2 oracle obligations without dispositions.",
    }
    (FROZEN / "freeze.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    _write_evidence_md(audit, meta)
    _write_cards_copy(cards)
    return meta


def _write_evidence_md(audit: list[dict], meta: dict) -> None:
    lines = [
        "# Evidence-sufficiency audit — Prose Probe v1",
        "",
        f"Frozen at `{meta['frozen_at']}`.",
        "",
        "Labels: **MEASURED** corpus presence. Classification is evaluator judgment of whether the GOLD-S semantic distinction can be established from participant sources without extra-corpus legends.",
        "",
        f"Establishable: **{meta['n_establishable']}/12**. Underdetermined: {meta['n_underdetermined']}. Not present: {meta['n_not_present']}.",
        "",
        "Primary scoring uses only `ESTABLISHABLE_FROM_PARTICIPANT_CORPUS`.",
        "",
        "| gold_id | purposes | source | classification |",
        "|---|---|---|---|",
    ]
    for row in audit:
        lines.append(
            f"| `{row['gold_id']}` | {', '.join(row['affected_purposes'])} | `{row['source_document']}` | `{row['classification']}` |"
        )
    lines.append("")
    for row in audit:
        lines.extend(
            [
                f"## {row['gold_id']}",
                "",
                f"- Affected purposes: {', '.join(row['affected_purposes'])}",
                f"- Source: `{row['source_document']}` — {row['source_locator']}",
                f"- Classification: `{row['classification']}`",
                "",
                row["reason"],
                "",
            ]
        )
        if row.get("closure_note"):
            lines.extend([f"*Closure note:* {row['closure_note']}", ""])
    (REPORTS / "evidence_sufficiency.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_cards_copy(cards: list[dict]) -> None:
    # protocol asks reports/semantic_cards.json as well
    (REPORTS / "semantic_cards.json").write_text(json.dumps(cards, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(freeze(), indent=2))
