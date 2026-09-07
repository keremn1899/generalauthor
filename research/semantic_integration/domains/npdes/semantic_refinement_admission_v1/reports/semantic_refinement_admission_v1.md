# Semantic Refinement & Admission Microprobe v1

Sealed interpretation: **REFINEMENT_ADMISSION_BOUNDARY_SUPPORTED**

Follow-up to Obligation-Driven Targeted Semantic Resolution Probe v1. Draft spine T5. Composer 2.5 only.
GOLD and expected.json were not shown to the host. Not constructor promotion. Research metadata only (`REFINED` is not a kernel primitive).

## Required answers

### 1. When evidence reveals heterogeneous semantics, does the host mark the parent as REFINED rather than UNRESOLVED?

MEASURED parent_statuses={
  "T1:geometric_mean": "REFINED",
  "T1:empty_numeric_limit": "REFINED",
  "T1:document_authority": "REFINED",
  "T2:geometric_mean": "REFINED",
  "T2:empty_numeric_limit": "REFINED",
  "T2:document_authority": "REFINED",
  "T3:geometric_mean": "REFINED",
  "T3:empty_numeric_limit": "REFINED",
  "T3:document_authority": "REFINED"
}
protocol_drifts=[]

### 2. Are child obligations reusable semantic questions rather than source-row special cases?

MEASURED compactness=[
  {
    "cell": "T1:geometric_mean",
    "n_children": 4,
    "largest": 24,
    "smallest": 4,
    "parent_occurrences": 40,
    "residual": [
      "3610673273|3600891019",
      "3610673274|3600891019",
      "3610673275|3600891019",
      "3610673276|3600891019",
      "3610673297|3600891019",
      "3610673299|3600891019",
      "3610838802|3600891019",
      "3610838804|3600891019"
    ],
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T1:empty_numeric_limit",
    "n_children": 4,
    "largest": 18,
    "smallest": 12,
    "parent_occurrences": 57,
    "residual": 0,
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T1:document_authority",
    "n_children": 5,
    "largest": 3,
    "smallest": 1,
    "parent_occurrences": 1,
    "residual": [],
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T2:geometric_mean",
    "n_children": 3,
    "largest": 24,
    "smallest": 4,
    "parent_occurrences": 40,
    "residual": 0,
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T2:empty_numeric_limit",
    "n_children": 4,
    "largest": 18,
    "smallest": 12,
    "parent_occurrences": 57,
    "residual": 0,
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T2:document_authority",
    "n_children": 5,
    "largest": 12,
    "smallest": 1,
    "parent_occurrences": 1,
    "residual": [
      {
        "child_id": "minor_modification_standalone_authority",
        "document_kind": "minor_modification",
        "permit": "NM0000116",
        "path": "sources/gcc/minor_modification.pdf"
      }
    ],
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T3:geometric_mean",
    "n_children": 3,
    "largest": 24,
    "smallest": 4,
    "parent_occurrences": 40,
    "residual": [],
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T3:empty_numeric_limit",
    "n_children": 4,
    "largest": 18,
    "smallest": 12,
    "parent_occurrences": 57,
    "residual": [],
    "mechanically_computable": true,
    "fragmented": false
  },
  {
    "cell": "T3:document_authority",
    "n_children": 5,
    "largest": 3,
    "smallest": 1,
    "parent_occurrences": 1,
    "residual": [
      {
        "child_id": "minor_modification_authority_unestablished",
        "occurrence_partition_rule": "document_inventory.json entry where permit == \"NM0000116\" and document_kind == \"minor_modification\"",
        "affected_count": 1,
        "reason": "No retrieved workspace text establishes incorporation, supersession, or explicit conflict precedence between minor_modification and final_permit for NM0000116."
      }
    ],
    "mechanically_computable": true,
    "fragmented": false
  }
]
fragmented=[]

### 3. Are partitions mechanically reconstructible?

See refinement_results.md `mechanically_computable` per cell.

### 4. Does geometric-mean refinement consistently recover TDS vs non-TDS?

MEASURED tds_split={
  "T1:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  },
  "T2:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  },
  "T3:geometric_mean": {
    "tds": true,
    "nontds": true,
    "recovered": true
  }
} recovered=3/3

### 5. Does empty-numeric-limit refinement stay compact?

See compactness rows for empty_numeric_limit. Flag OCCURRENCE_LEVEL_FRAGMENTATION only if unique-row children.

### 6. Can individual children resolve while sibling children remain unresolved?

See child disposition/admission mix in refinement_results.md (residual UNRESOLVED is allowed).

### 7. Does disposable propagation affect only the intended child population?

leakage={} failed_dry=[]

### 8. Are there any parent/child admission contradictions?

MEASURED protocol_drifts=[] unsupported_child_closures=[]

### 9–12. Document-role local vs general

See document_admission_results.md.
broader_admissions=[] local_underused=[]

### 13. Unsupported broader closures?

MEASURED []

### 14–15. Frontier compilation and scope vs admission

Interpretation: **REFINEMENT_ADMISSION_BOUNDARY_SUPPORTED**. H1/H2 are supported only if refined parents are superseded and local vs general admission stays distinct.

## Interpretation

**REFINEMENT_ADMISSION_BOUNDARY_SUPPORTED**

## STOP

No constructor/kernel change. REFINED is research metadata only. No semantic-family taxonomy. No retrieval-architecture change. No UI. No P5. No fifth domain. No real-user study.
