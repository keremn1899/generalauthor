"""Construction-boundary runtime for Worlds.

A capable agent may author ordinary Python that explores sources and commits a
candidate World. This package is a supported *mechanism* for that boundary, not
a semantic primitive and not a required filename. See the attached capability
contract for the construction boundary.

The semantic core does not import this construction package.
"""

from ontology_author.world.runtime.commit import RunResult
from ontology_author.world.runtime.entry import create, open_world, rebuild
from ontology_author.world.runtime.project import Project
from ontology_author.world.runtime.purpose import FAILURE_RELATION, Purpose
from ontology_author.world.runtime.source_helpers import Source
from ontology_author.world.runtime.world import ConstructionError, ConstructionWorld, GroundingError

__all__ = [
    "ConstructionError",
    "ConstructionWorld",
    "FAILURE_RELATION",
    "GroundingError",
    "Project",
    "Purpose",
    "RunResult",
    "Source",
    "create",
    "open_world",
    "rebuild",
]
