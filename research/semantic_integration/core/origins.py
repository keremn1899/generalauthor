"""Construction-origin axis used by the experimental harness.

This is not TaskView's ASSERTED/DERIVED bookkeeping.  It classifies how a live
semantic tuple entered the world so frontier size can be computed mechanically.
"""

from __future__ import annotations

from enum import StrEnum


class ConstructionOrigin(StrEnum):
    MECHANICAL = "MECHANICAL"
    SEMANTIC = "SEMANTIC"
    DERIVED = "DERIVED"


class OriginMetadataError(ValueError):
    """An asserted tuple has no recorded construction origin."""
