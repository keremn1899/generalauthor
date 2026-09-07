# Purpose D — held-out compliance follow-up

Identify FY2025 facility/discharge-point/parameter/monitoring-period combinations requiring compliance follow-up because either:

1. an enforceable applicable numeric limit was exceeded, or
2. monitoring was required but the available evidence does not adequately establish the required observation.

Exclude report-only measurements from numeric exceedance findings. Exclude periods where the evidence establishes that monitoring was legitimately not required or that there was no discharge when that removes the monitoring obligation. Preserve unresolved cases separately rather than classifying them automatically as violations.

Write purpose_ir/d/output.json and 08_outputs/d.json as a JSON object with:
- purpose: compliance_follow_up
- follow_up: list of combinations requiring follow-up, each with reason exceedance | missing_required_monitoring
- unresolved: list of cases preserved as unresolved
- excluded: list of cases excluded because report-only, not required, or no discharge
