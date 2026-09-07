# Semantic header

## PURPOSE

Determine which tool checkouts are authorized, what fees apply under shop rules (including identity changes and after-hours), and where notes or coverage questions remain insufficiently evidenced.

## WORLD CONTRACT

No rows are included. Meanings are constructor-authored; empty means none was provided.

### checkout_authorization
meaning: (none provided)
roles: checkout:REFERENT, status:TEXT, basis:TEXT
scope: PURPOSE
mode: BASE

### checkout_fee
meaning: (none provided)
roles: checkout:REFERENT, resolved_tool:REFERENT, hourly_rate:TEXT, hours:TEXT, after_hours_multiplier:TEXT, total_fee:TEXT
scope: PURPOSE
mode: BASE

### checkout_record
meaning: (none provided)
roles: checkout:REFERENT, member:REFERENT, tool_id:TEXT, out_time:TEXT, in_time:TEXT, note:TEXT, hours_marked:TEXT
scope: WORLD
mode: BASE

### member_record
meaning: (none provided)
roles: member:REFERENT, name:TEXT, certs:TEXT
scope: WORLD
mode: BASE

### purpose_requirement_failure
meaning: Purpose requirement failures. Ordinary relation, not a kernel primitive.
roles: requirement_id:TEXT, affected_identity:TEXT, failure_kind:TEXT, relation_name:TEXT, subject_json:TEXT, grounding_ref:TEXT
scope: PURPOSE
mode: BASE

### tool_identity_remap
meaning: (none provided)
roles: from_tool_id:TEXT, to_tool:REFERENT
scope: WORLD
mode: BASE

### tool_record
meaning: (none provided)
roles: tool:REFERENT, name:TEXT, cert_required:TEXT, hourly_fee:TEXT
scope: WORLD
mode: BASE

## READ RULES

Unresolved / insufficient / unknown / uninterpreted is not false.

An empty result alone means no matching tuple was observed, not established absence.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.

## REVISION

view_id=v0; schema_revision=42
