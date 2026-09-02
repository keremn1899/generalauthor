"""Provider-native observation and assertion-grounding contract.

Evidence state stays outside semantic assertion state.  Grounding points at
observations; it does not copy source bodies into the relation tuple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SourceObservation:
    provider: str
    native_handle: str
    source_revision: str
    native_location: str
    payload: str = ""

    def as_pointer(self) -> dict[str, str]:
        return {
            "provider": self.provider,
            "native_handle": self.native_handle,
            "source_revision": self.source_revision,
            "native_location": self.native_location,
        }


@dataclass(frozen=True)
class AssertionGrounding:
    observations: tuple[SourceObservation, ...]
    construction_method: str = ""
    extra: dict[str, Any] | None = None
