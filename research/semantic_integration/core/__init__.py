"""Thin World IR wrap over the existing TaskView store.

Not a second calculus. See CONSTITUTION.md.
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
