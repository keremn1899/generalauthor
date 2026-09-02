"""Research-only semantic-integration kernel and C0/C1/C2 harness.

This package wraps TaskView. It is not a product surface and does not replace
``taskview``.
"""

from research.semantic_integration.core.kernel import SemanticWorld
from research.semantic_integration.core.origins import ConstructionOrigin, OriginMetadataError
from research.semantic_integration.core.source import AssertionGrounding, SourceObservation

__all__ = [
    "AssertionGrounding",
    "ConstructionOrigin",
    "OriginMetadataError",
    "SemanticWorld",
    "SourceObservation",
]
