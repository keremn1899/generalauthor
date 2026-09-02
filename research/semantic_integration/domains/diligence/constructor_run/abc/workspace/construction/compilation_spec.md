# Compilation specification

## Evaluation date

Mechanical contract-active status is evaluated on **2025-09-01** (task date).

## Construction phases

| Phase | Responsibility | Output relations |
|-------|----------------|------------------|
| C0 | Thin referents from each source row/document | referents in `_tv_referents` |
| C1 | Mechanical parsing, joins, normalization | WORLD BASE relations |
| C2 | Semantic frontier obligations | `construction/semantic_frontier/obligations.json` |
| C3 | Grounded resolution | `identity_judgment`, `world/obligations.json` |
| C4 | SQL/Python derivations | PURPOSE DERIVED relations and `purpose_ir/*/output.json` |

## WORLD vs PURPOSE

**WORLD** holds source-true facts: CRM rows, invoices, registry, contract headers/clauses, mechanical candidates, and resolved identity judgments grounded in evidence.

**PURPOSE** holds analytical projections: acquisition-relevance filter (A), identity link export (B), commercial dependency (C).

## Identity policy

- Exact legal-form normalization (Ltd/Limited/Inc/LLC/GmbH punctuation) is mechanical.
- Commercial notes may ground SAME_ENTITY or DISTINCT when authoritative.
- Multiple registry entities with similar trade names remain UNRESOLVED unless grounded.
- No closed-world DISTINCT: absence of judgment stays UNRESOLVED.

## Contract activity

- `SOW-VEL-2022` expired 2023-12-31 → inactive.
- Rolling and auto-renewing MSAs without lapse → active.

## Acquisition relevance (Purpose A)

Maps WORLD `contract_clause.clause_kind` to acquisition relevance:

- `change_of_control_consent`, `change_of_control_termination`
- `assignment_consent_required`, `assignment_notice_required`, `assignment_competitor_prohibition`

Excludes silent/none/unrestricted clauses and exclusivity (Purpose C only).

## Commercial dependency (Purpose C)

`obligation_kinds` drawn from `contract_term_kind` (`auto_renewal`, `rolling_term`) and `contract_clause` (`exclusivity`).

Current relationship: open invoice **or** active contract with auto-renewal/rolling term.
