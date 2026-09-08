"""Construction-origin axis used by the experimental harness.

This is separate from ASSERTED/DERIVED assertion bookkeeping. It classifies how a live
semantic tuple entered the world so frontier size can be computed mechanically.
"""

from __future__ import annotations

from enum import StrEnum


class ConstructionOrigin(StrEnum):
    """How a live semantic tuple came to be in the world.

    ``ADJUDICATED`` is a person's judgment, superseding or supplying one the
    constructor made.  It is its own member rather than a flavour of
    ``SEMANTIC`` because a human decision entering as the machine's launders
    it: every downstream claim about how the world was constructed becomes
    untrue, and the frontier stops being computable mechanically.
    """

    MECHANICAL = "MECHANICAL"
    SEMANTIC = "SEMANTIC"
    DERIVED = "DERIVED"
    ADJUDICATED = "ADJUDICATED"


class OriginMetadataError(ValueError):
    """An asserted tuple has no recorded construction origin."""
