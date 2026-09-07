# Semantic header

## PURPOSE

Determine remaining award balances, which cash-match rules apply, and which award statuses can be interpreted from the office legend. Expose cases where the packet is insufficient to classify status or match obligations confidently.

## WORLD CONTRACT

No rows are included. Meanings are constructor-authored; empty means none was provided.

### award
meaning: (none provided)
roles: award_id:TEXT, org_id:TEXT, program:TEXT, amount:TEXT, start:TEXT, end:TEXT, status_code:TEXT
scope: WORLD
mode: BASE

### award_match_obligation
meaning: (none provided)
roles: award_id:TEXT, program:TEXT, match_required:TEXT, match_rate:TEXT
scope: WORLD
mode: BASE

### award_remaining_balance
meaning: (none provided)
roles: award_id:TEXT, award_amount:TEXT, disbursed_total:TEXT, remaining_balance:TEXT
scope: WORLD
mode: BASE

### award_status_label
meaning: (none provided)
roles: award_id:TEXT, status_code:TEXT, status_label:TEXT
scope: WORLD
mode: BASE

### disbursement
meaning: (none provided)
roles: award_id:TEXT, date:TEXT, amount:TEXT
scope: WORLD
mode: BASE

### organization
meaning: (none provided)
roles: org_id:TEXT, legal_name:TEXT, ein:TEXT
scope: WORLD
mode: BASE

### program_match_rule
meaning: (none provided)
roles: program:TEXT, match_required:TEXT, match_rate:TEXT, waiver_possible:TEXT
scope: WORLD
mode: BASE

### purpose_requirement_failure
meaning: Purpose requirement failures. Ordinary relation, not a kernel primitive.
roles: requirement_id:TEXT, affected_identity:TEXT, failure_kind:TEXT, relation_name:TEXT, subject_json:TEXT, grounding_ref:TEXT
scope: PURPOSE
mode: BASE

### status_legend_entry
meaning: (none provided)
roles: code:TEXT, meaning:TEXT
scope: WORLD
mode: BASE

## READ RULES

Unresolved / insufficient / unknown / uninterpreted is not false.

An empty result alone means no matching tuple was observed, not established absence.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.

## REVISION

view_id=v0; schema_revision=46
