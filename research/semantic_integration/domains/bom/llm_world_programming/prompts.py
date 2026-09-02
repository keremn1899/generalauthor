"""Shared and condition-specific prompts.  Same analytical objective in both arms."""

from __future__ import annotations

IDENTITY = """Identifiers in the JSON result must use these forms:
- parts: "part:<part_number>"
- BOM items: "bom:<bom_item>"
- contexts: "context:<deployment_environment>"
- listings: "listing:<sku>"
"""

SAVE = """Save the Python program as analysis.py in the workspace root.
Write the JSON result to output.json in the workspace root.
The program must be executable: a later scorer will run analysis.py in a clean copy of this environment.
Do not hard-code an answer you did not compute.
"""

ORIENT_RAW = (
    "The authoritative input files available in this workspace contain the "
    "information required for this analysis. Write Python to inspect them and "
    "produce the requested JSON output."
)

ORIENT_WORLD = (
    "A compiled semantic World containing the information required for this "
    "analysis is available through the documented Python/SQL interface. Write "
    "Python to inspect it and produce the requested JSON output."
)

TASK_A = """# Task: replacement state

Determine the current state of represented replacement candidates under the
deployment contexts they apply to.

For each candidate/context case, report:
- new part, old part, and context
- BOM items in that context
- whether the new part is mechanically suitable for those BOM items
- semantic acceptance state
- an epistemic class

Do not treat missing acceptance as false. Missing a positive acceptance
judgment is not the same as a negative judgment.

""" + IDENTITY + """
Core JSON shape (this is the scored payload; extra keys are ignored except as noted):

{
  "task": "replacement_state",
  "cases": [
    {
      "new_part": string,
      "old_part": string,
      "context": string,
      "bom_items": [string],
      "mechanical_state": "suitable" | "unsuitable",
      "semantic_state": "accepted" | "unresolved" | "not_established",
      "epistemic": "ASSERTED_TRUE" | "UNRESOLVED" | "NOT_KNOWN"
    }
  ]
}

Sort cases by new_part, old_part, context. Sort bom_items lexicographically.

Provenance subtest (scored separately; do not omit the core fields):
Also include a top-level "support" array tracing one case to authoritative
evidence. Each item:

{"claim": string, "evidence": [{"source": string, "locator": string}]}

Do not write a prose explanation.
"""

TASK_B = """# Task: qualification bottlenecks

For represented replacement candidates, determine which constraints prevent
viability or leave viability uncertain under each relevant BOM item/context.

Distinguish actual failed/preventing constraints from semantic uncertainty.
A missing positive semantic-acceptance judgment is not by itself a failed
qualification constraint.

""" + IDENTITY + """
JSON shape:

{
  "task": "qualification_bottlenecks",
  "cases": [
    {
      "new_part": string,
      "old_part": string,
      "bom_item": string,
      "context": string,
      "voltage_compatible": boolean,
      "temperature_compatible": boolean,
      "new_part_lifecycle_active": boolean,
      "old_part_lifecycle": string,
      "semantic_state": "accepted" | "unresolved" | "not_established",
      "prevents_viability": [string],
      "leaves_viability_uncertain": [string]
    }
  ]
}

Sort cases by new_part, old_part, bom_item, context.
Use "voltage_compatible", "temperature_compatible", "lifecycle_active", and
"semantic_acceptance" as constraint names in the two lists when applicable.
"""

TASK_C = """# Task: specification-conflict review

Identify represented specification conflicts for parts and their relationship
to represented BOM requirements and eligibility.

""" + IDENTITY + """
JSON shape:

{
  "task": "spec_conflict_review",
  "conflicts": [
    {
      "part": string,
      "property": string,
      "values": [number],
      "matching_bom_items": [string],
      "eligible_bom_items": [string],
      "listings_of_part": [{"listing": string, "availability": string}],
      "observation_sources": [{"volts": number, "source": string}],
      "review": "conflicting_rated_voltage_observations"
    }
  ]
}

Sort conflicts by part, property. Sort lists lexicographically except values
and observation_sources, which are sorted by numeric value (then source).
"""

TASKS = {
    "analysis_a": TASK_A,
    "analysis_b": TASK_B,
    "analysis_c": TASK_C,
}


def participant_prompt(condition: str, task_id: str) -> str:
    orientation = ORIENT_RAW if condition == "raw" else ORIENT_WORLD
    return (
        orientation
        + "\n\n"
        + TASKS[task_id]
        + "\n"
        + SAVE
    )
