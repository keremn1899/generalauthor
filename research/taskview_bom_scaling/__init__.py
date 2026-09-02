"""Controlled scaling and bounded-adjudication preflight for the BOM spike."""

EXPERIMENT_ID = "taskview-bom-scaling-v1"
BASELINE_ORACLE_ID = "taskview-bom-c0-v1"
SCALE_SEED = 20260901

SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED = False
PROVIDER_INFERENCE_CALLS = 0

__all__ = [
    "BASELINE_ORACLE_ID",
    "EXPERIMENT_ID",
    "PROVIDER_INFERENCE_CALLS",
    "SCALE_SEED",
    "SEMANTIC_FRONTIER_INFERENCE_AUTHORIZED",
]
