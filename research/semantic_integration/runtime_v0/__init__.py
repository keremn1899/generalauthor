"""Construction-boundary runtime over TaskView.

A capable agent may author ordinary Python that explores sources and commits a
candidate World. This package is a supported *mechanism* for that boundary, not
a semantic primitive and not a required filename. See CONSTRUCTION.md.

TaskView must not import this package.
"""

from research.semantic_integration.runtime_v0.commit import RunResult, publish_candidate
from research.semantic_integration.runtime_v0.project import Project
from research.semantic_integration.runtime_v0.purpose import FAILURE_RELATION, Purpose
from research.semantic_integration.runtime_v0.source_helpers import Source
from research.semantic_integration.runtime_v0.world import ConstructionError, ConstructionWorld, GroundingError

__all__ = [
    "ConstructionError",
    "ConstructionWorld",
    "FAILURE_RELATION",
    "GroundingError",
    "Project",
    "Purpose",
    "RunResult",
    "Source",
    "publish_candidate",
]
