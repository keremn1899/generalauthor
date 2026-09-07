# Semantic header

## PURPOSE

Determine which towing jobs are billable under which rates, apply the harbor's service conditions, and expose cases where the available evidence is insufficient to calculate a charge confidently.

## WORLD CONTRACT

No rows are included. Meanings are constructor-authored; empty means none was provided.

### berth_restriction
meaning: Berth operating restrictions from berth_notice.txt.
roles: berth:TEXT, restriction:TEXT
scope: WORLD
mode: BASE

### billable_hours
meaning: Established billable hours for a job.
roles: job:REFERENT, hours:REAL, basis:TEXT
scope: PURPOSE
mode: BASE

### billing_outcome
meaning: Whether a job is billable, not billable, or insufficiently evidenced.
roles: job:REFERENT, status:TEXT, reason:TEXT
scope: PURPOSE
mode: BASE

### effective_rate
meaning: Applicable hourly rate for a job after service conditions.
roles: job:REFERENT, rate_service_code:TEXT, rate_per_hour:REAL, basis:TEXT
scope: PURPOSE
mode: BASE

### job_charge
meaning: Computed charge when evidence supports confident billing.
roles: job:REFERENT, charge:REAL, basis:TEXT
scope: PURPOSE
mode: BASE

### purpose_requirement_failure
meaning: Purpose requirement failures. Ordinary relation, not a kernel primitive.
roles: requirement_id:TEXT, affected_identity:TEXT, failure_kind:TEXT, relation_name:TEXT, subject_json:TEXT, grounding_ref:TEXT
scope: PURPOSE
mode: BASE

### rate_card
meaning: Published hourly rates from rate_card.csv.
roles: service_code:TEXT, name:TEXT, rate_per_hour:REAL, minimum_hours:REAL
scope: WORLD
mode: BASE

### tow_job
meaning: Towing job records from jobs.csv.
roles: job:REFERENT, vessel_id:TEXT, berth:TEXT, start_time:TEXT, end_time:TEXT, service_code:TEXT, billed_hours:TEXT, comment:TEXT
scope: WORLD
mode: BASE

### vessel
meaning: Vessel registry from vessels.csv.
roles: vessel:REFERENT, vessel_class:TEXT, home_port:TEXT, display_name:TEXT
scope: WORLD
mode: BASE

## READ RULES

Unresolved / insufficient / unknown / uninterpreted is not false.

An empty result alone means no matching tuple was observed, not established absence.

PURPOSE relations are purpose-specific analytical state and do not replace more direct WORLD facts.

Unknown neighboring propositions do not invalidate independently established propositions unless an explicit dependency says so.

Inspect grounding when evidential status matters.

## REVISION

view_id=v0; schema_revision=50
