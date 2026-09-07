# Document admission results

## MEASURED

### T1

```json
{
  "ESTABLISHED_PROPOSITIONS": [
    {
      "proposition": "Issued final_permit cover pages authorize discharge only under conditions set forth in named Parts I\u2013III/IV 'hereof'.",
      "semantic_scope": "document_kind=final_permit for permits NM0000116, NM0020583, NM0028762",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "GCC and Farmington issued permits cross-reference Appendix A of Part II within the permit text, incorporating part_ii_appendix content.",
      "semantic_scope": "document_kind=part_ii_appendix paired with same-permit final_permit",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "Farmington issued permit references Part IV reporting requirements, incorporating part_iv content.",
      "semantic_scope": "document_kind=part_iv for permit NM0020583",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "GCC fact_sheet Section V is titled 'DRAFT PERMIT RATIONALE AND PROPOSED PERMIT CONDITIONS'.",
      "semantic_scope": "documents/gcc/fact_sheet.txt",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "Aztec statement_of_basis Section F defers final effluent limitations: 'See the draft permit for limitations.'",
      "semantic_scope": "documents/aztec/statement_of_basis.txt",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "Farmington statement_of_basis header text reads 'FACT SHEET' despite document_kind=statement_of_basis in inventory.",
      "semantic_scope": "documents/farmington/statement_of_basis.txt",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    },
    {
      "proposition": "Aztec reasonable_potential identifies itself as 'APPENDIX A of FACT SHEET'.",
      "semantic_scope": "documents/aztec/reasonable_potential.txt",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE"
    }
  ],
  "GENERALIZATIONS_CONSIDERED": [
    {
      "proposition": "Filename document_kind from document_inventory.json establishes authority hierarchy among package documents.",
      "semantic_scope": "KIND_OR_CORPUS_LOCAL \u2014 all 12 inventoried files",
      "epistemic_basis": "MODEL_GENERALIZATION"
    },
    {
      "proposition": "Issued final_permit always prevails over any other package document on conflict.",
      "semantic_scope": "KIND_OR_CORPUS_LOCAL \u2014 this 12-document permit package corpus",
      "epistemic_basis": "MODEL_GENERALIZATION"
    },
    {
      "proposition": "All NPDES permit packages follow the issued-permit self-defined corpus pattern.",
      "semantic_scope": "WORLD \u2014 NPDES permit packages generally",
      "epistemic_basis": "MODEL_GENERALIZATION"
    }
  ],
  "GENERALIZATIONS_ADMITTED": [],
  "GENERALIZATIONS_WITHHELD": [
    {
      "why_plausible": "Three final_permit files consistently self-define Parts I\u2013III/IV; supporting docs use draft/proposed framing.",
      "evidence_needed": "Explicit conflict-resolution language or minor_modification incorporation text for the full 12-file corpus.",
      "why_insufficient": "Functional precedence is established for examined partitions but minor_modification authority is unresolved and no explicit inter-document conflict clause was found."
    },
    {
      "why_plausible": "Farmington statement_of_basis is labeled FACT SHEET in its own header, undermining kind-as-hierarchy.",
      "evidence_needed": "A workspace rule or EPA guidance file in this corpus defining document_kind precedence.",
      "why_insufficient": "No workspace text ranks document_kind values; only local self-descriptions were found."
    },
    {
      "why_plausible": "Observed pattern matches common NPDES package structure.",
      "evidence_needed": "Corpus beyond these three permits or an in-workspace general rule document.",
      "why_insufficient": "Only three permits and twelve files are in scope; WORLD generalization lacks SOURCE_ESTABLISHED grounding."
    }
  ],
  "LEVELS": {
    "LEVEL_1_DOCUMENT_LOCAL": [
      {
        "proposition": "GCC final_permit authorizes discharge under Parts I, II, and III hereof.",
        "semantic_scope": "documents/gcc/final_permit.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "Aztec statement_of_basis defers final effluent limitations to the draft permit.",
        "semantic_scope": "documents/aztec/statement_of_basis.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "GCC minor_modification contains Part I limitation tables but no retrieved linkage to final_permit supersession.",
        "semantic_scope": "documents/gcc/minor_modification.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      }
    ],
    "LEVEL_2_KIND_OR_CORPUS_LOCAL": [
      {
        "proposition": "document_kind=final_permit rows self-define the governing permit corpus via cover-page part references.",
        "semantic_scope": "12-document permit package corpus partitioned by document_kind",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "document_kind in {fact_sheet, statement_of_basis, reasonable_potential} does not independently establish binding effluent limitations.",
        "semantic_scope": "12-document permit package corpus",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "Issued final_permit prevails on all inter-document conflicts in this corpus.",
        "semantic_scope": "12-document permit package corpus",
        "epistemic_basis": "MODEL_GENERALIZATION",
        "admission_status": "UNVERIFIED_PROPOSAL"
      }
    ],
    "LEVEL_3_GENERAL": [
      {
        "proposition": "NPDES permit packages universally treat final_permit as the sole binding authorization document.",
        "semantic_scope": "WORLD \u2014 NPDES permit packages",
        "epistemic_basis": "MODEL_GENERALIZATION",
        "admission_status": "UNVERIFIED_PROPOSAL"
      }
    ]
  }
}
```

### T2

```json
{
  "ESTABLISHED_PROPOSITIONS": [
    {
      "proposition": "Issued final_permit cover pages authorize discharge only under named Parts 'hereof' (Parts I\u2013III, or I\u2013IV for Farmington).",
      "scope": "document_kind=final_permit",
      "grounding": [
        "documents/gcc/final_permit.txt",
        "documents/farmington/final_permit.txt",
        "documents/aztec/final_permit.txt"
      ]
    },
    {
      "proposition": "Part II appendices are incorporated into the issued permit by internal cross-reference to 'Appendix A of Part II of this permit.'",
      "scope": "document_kind=part_ii_appendix",
      "grounding": [
        "documents/gcc/final_permit.txt",
        "documents/farmington/final_permit.txt"
      ]
    },
    {
      "proposition": "Farmington Part IV is part of the governing corpus via cover-page reference to 'Part IV hereof.'",
      "scope": "document_kind=part_iv, permit NM0020583",
      "grounding": [
        "documents/farmington/final_permit.txt"
      ]
    },
    {
      "proposition": "Fact sheets and statements of basis frame content as draft/proposed rationale and administrative record, not standalone authorization.",
      "scope": "document_kind in (fact_sheet, statement_of_basis)",
      "grounding": [
        "documents/gcc/fact_sheet.txt",
        "documents/farmington/statement_of_basis.txt",
        "documents/aztec/statement_of_basis.txt"
      ]
    },
    {
      "proposition": "Reasonable-potential files are calculation appendices to fact sheets, not independent authorization documents.",
      "scope": "document_kind=reasonable_potential",
      "grounding": [
        "documents/aztec/reasonable_potential.txt",
        "documents/gcc/reasonable_potential.txt"
      ]
    },
    {
      "proposition": "Inventory document_kind can mismatch document header text (Farmington statement_of_basis labeled FACT SHEET).",
      "scope": "corpus_local",
      "grounding": [
        "documents/farmington/statement_of_basis.txt",
        "sources/document_inventory.json"
      ]
    }
  ],
  "GENERALIZATIONS_CONSIDERED": [
    "Global NPDES package document-kind precedence hierarchy",
    "All package documents are co-equal binding authority absent explicit conflict clause",
    "Minor modification files are automatically incorporated into final permits when Part I text overlaps"
  ],
  "GENERALIZATIONS_ADMITTED": [],
  "GENERALIZATIONS_WITHHELD": [
    {
      "generalization": "Global NPDES package document-kind precedence hierarchy (final_permit > fact_sheet > statement_of_basis > reasonable_potential)",
      "why_plausible": "Inventory uses consistent kind labels across permits; filenames suggest document roles.",
      "evidence_needed": "Workspace regulatory or package text ranking kinds, or consistent precedence language across all permits.",
      "why_insufficient": "No workspace text ranks kinds; Farmington statement_of_basis header is FACT SHEET; supporting documents use draft/proposed framing."
    },
    {
      "generalization": "All twelve inventoried files are independently binding with no functional precedence",
      "why_plausible": "No explicit 'in the event of conflict' clause was found.",
      "evidence_needed": "Text showing supporting documents independently authorize discharge or set final limitations.",
      "why_insufficient": "Issued permits self-define governing Parts; supporting documents defer limitations to draft/issued permit."
    },
    {
      "generalization": "Minor modification Part I extracts automatically govern or amend the issued final permit when text parallels Part I",
      "why_plausible": "documents/gcc/minor_modification.txt Part I parallels documents/gcc/final_permit.txt Part I opening.",
      "evidence_needed": "Incorporation, supersession, or effective-date amendment language in final_permit or minor_modification linking the files.",
      "why_insufficient": "No cross-reference from final_permit to minor_modification; standalone authority unestablished."
    }
  ],
  "LEVELS": {
    "LEVEL_1_DOCUMENT_LOCAL": [
      {
        "proposition": "GCC final_permit cover page limits authorization to Parts I\u2013III hereof.",
        "semantic_scope": "documents/gcc/final_permit.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "Aztec statement_of_basis Section F defers final effluent limitations to the draft permit.",
        "semantic_scope": "documents/aztec/statement_of_basis.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "GCC minor_modification standalone authority relative to final_permit is unestablished.",
        "semantic_scope": "documents/gcc/minor_modification.txt",
        "epistemic_basis": "UNRESOLVED",
        "admission_status": "UNRESOLVED"
      }
    ],
    "LEVEL_2_KIND_OR_CORPUS_LOCAL": [
      {
        "proposition": "document_kind=final_permit identifies issued governing corpus via cover-page Part enumeration.",
        "semantic_scope": "all final_permit entries in this workspace inventory",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "document_kind in (fact_sheet, statement_of_basis, reasonable_potential) marks supporting explanatory package material that defers enforceable limitations to the issued permit.",
        "semantic_scope": "all supporting-kind entries in this workspace inventory",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "document_kind labels alone do not establish conflict precedence in this corpus.",
        "semantic_scope": "all twelve inventoried documents",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      }
    ],
    "LEVEL_3_GENERAL": [
      {
        "proposition": "NPDES permit packages universally resolve document authority by filename kind hierarchy.",
        "semantic_scope": "WORLD",
        "epistemic_basis": "MODEL_GENERALIZATION",
        "admission_status": "UNVERIFIED_PROPOSAL"
      },
      {
        "proposition": "Issued permit cover-page Part enumeration is the default governing-corpus rule for NPDES packages.",
        "semantic_scope": "WORLD",
        "epistemic_basis": "MODEL_GENERALIZATION",
        "admission_status": "UNVERIFIED_PROPOSAL"
      }
    ]
  }
}
```

### T3

```json
{
  "ESTABLISHED_PROPOSITIONS": [
    {
      "proposition": "Issued final_permit cover pages authorize discharge under named internal parts hereof (Parts I\u2013III/IV).",
      "semantic_scope": "documents where document_kind=final_permit in this workspace",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "grounding": [
        "documents/gcc/final_permit.txt lines 19-21",
        "documents/farmington/final_permit.txt lines 24-25",
        "documents/aztec/final_permit.txt lines 32-33"
      ]
    },
    {
      "proposition": "Part II appendix and Part IV inventoried files are incorporated into the issued final_permit by internal cross-reference.",
      "semantic_scope": "documents where document_kind in (part_ii_appendix, part_iv) in this workspace",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "grounding": [
        "documents/gcc/final_permit.txt lines 149-150",
        "documents/farmington/final_permit.txt lines 25 and 213"
      ]
    },
    {
      "proposition": "Fact sheets and statements of basis use draft/proposed framing and defer enforceable limitations to the permit.",
      "semantic_scope": "documents where document_kind in (fact_sheet, statement_of_basis) in this workspace",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "grounding": [
        "documents/gcc/fact_sheet.txt line 191",
        "documents/aztec/statement_of_basis.txt lines 556-558",
        "documents/farmington/statement_of_basis.txt lines 1-5"
      ]
    },
    {
      "proposition": "Reasonable-potential files are calculation appendices, not standalone authorization documents.",
      "semantic_scope": "documents where document_kind=reasonable_potential in this workspace",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "grounding": [
        "documents/aztec/reasonable_potential.txt lines 12-13",
        "documents/gcc/reasonable_potential.txt lines 4-5"
      ]
    },
    {
      "proposition": "Inventory document_kind labels alone do not determine document authority or conflict precedence.",
      "semantic_scope": "all entries in sources/document_inventory.json",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "grounding": [
        "documents/farmington/statement_of_basis.txt lines 1-3 FACT SHEET header",
        "sources/document_inventory.json (kind labels without precedence metadata)"
      ]
    }
  ],
  "GENERALIZATIONS_CONSIDERED": [
    {
      "proposition": "Across NPDES permit packages, final_permit always governs over fact_sheet, statement_of_basis, reasonable_potential, and incorporated parts when package documents disagree.",
      "scope": "LEVEL_3_GENERAL / WORLD"
    },
    {
      "proposition": "Minor modifications always supersede the base final_permit unless an explicit incorporation clause says otherwise.",
      "scope": "LEVEL_3_GENERAL / WORLD"
    },
    {
      "proposition": "Precedence requires an explicit 'in the event of conflict' clause; without one no functional precedence exists.",
      "scope": "LEVEL_3_GENERAL / WORLD"
    },
    {
      "proposition": "Within this three-permit inventory, issued final_permit plus incorporated parts form the enforceable corpus and supporting document kinds defer to it.",
      "scope": "LEVEL_2_KIND_OR_CORPUS_LOCAL"
    }
  ],
  "GENERALIZATIONS_ADMITTED": [
    {
      "proposition": "Within this three-permit inventory, issued final_permit defines the primary authorization corpus; part_ii_appendix and part_iv are incorporated by cross-reference; fact_sheet, statement_of_basis, and reasonable_potential are supporting subordinate documents.",
      "scope": "LEVEL_2_KIND_OR_CORPUS_LOCAL",
      "epistemic_basis": "SOURCE_ESTABLISHED",
      "admission_status": "ADMIT_DISPOSABLE",
      "note": "Licensed only by repeated document-local patterns across NM0000116, NM0020583, and NM0028762 in this workspace."
    }
  ],
  "GENERALIZATIONS_WITHHELD": [
    {
      "proposition": "Across all NPDES permit packages, final_permit always governs over supporting package documents when they disagree.",
      "why_plausible": "All three final_permits in this inventory self-define authorization by internal parts; supporting documents defer in retrieved text.",
      "evidence_needed": "Explicit regulatory or multi-corpus workspace rule beyond these three permits.",
      "why_insufficient": "Observations are document-local and repeated only within this bounded inventory; no workspace file states a universal precedence rule."
    },
    {
      "proposition": "Minor modifications always supersede the base final_permit.",
      "why_plausible": "minor_modification.txt for NM0000116 contains Part I authorization language resembling a permit.",
      "evidence_needed": "Retrieved incorporation, supersession, or effective-date conflict language linking minor_modification to final_permit.",
      "why_insufficient": "final_permit text retrieved does not reference minor_modification; no explicit conflict clause was found."
    },
    {
      "proposition": "Precedence is unknowable without an explicit inter-document conflict clause.",
      "why_plausible": "No package-wide 'in the event of conflict' clause was retrieved.",
      "evidence_needed": "Demonstration that functional precedence cannot be read from issued-permit self-definition and supporting-document deferral.",
      "why_insufficient": "Issued-permit cover pages and supporting-document deferral language establish functional precedence for most partitions without a named conflict clause."
    }
  ],
  "LEVELS": {
    "LEVEL_1_DOCUMENT_LOCAL": [
      {
        "proposition": "GCC final_permit authorizes discharge under Parts I\u2013III hereof.",
        "semantic_scope": "documents/gcc/final_permit.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "Farmington final_permit authorizes discharge under Parts I\u2013IV hereof.",
        "semantic_scope": "documents/farmington/final_permit.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "Aztec statement_of_basis defers final effluent limitations to the draft permit.",
        "semantic_scope": "documents/aztec/statement_of_basis.txt Section F",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      },
      {
        "proposition": "GCC minor_modification contains Part I authorization text but is not referenced by retrieved final_permit text.",
        "semantic_scope": "documents/gcc/minor_modification.txt relative to documents/gcc/final_permit.txt",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      }
    ],
    "LEVEL_2_KIND_OR_CORPUS_LOCAL": [
      {
        "proposition": "document_kind=final_permit entries define the issued authorization corpus by internal parts; document_kind in (part_ii_appendix, part_iv) are incorporated parts; document_kind in (fact_sheet, statement_of_basis, reasonable_potential) are supporting subordinate documents within this inventory.",
        "semantic_scope": "all twelve entries in sources/document_inventory.json except unresolved minor_modification precedence",
        "epistemic_basis": "SOURCE_ESTABLISHED",
        "admission_status": "ADMIT_DISPOSABLE"
      }
    ],
    "LEVEL_3_GENERAL": [
      {
        "proposition": "Universal NPDES package-document precedence follows document_kind filename ordering.",
        "semantic_scope": "WORLD",
        "epistemic_basis": "MODEL_GENERALIZATION",
        "admission_status": "UNVERIFIED_PROPOSAL"
      },
      {
        "proposition": "Universal rule that final_permit always governs 
```

## OBSERVED

broader_admissions=[]
local_underused=[]

## HYPOTHESIS

Local source-established observations may be admitted. Broader inferred precedence remains UNVERIFIED_PROPOSAL unless licensed.
