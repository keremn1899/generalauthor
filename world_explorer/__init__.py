"""Read-side explorer surface over a compiled World IR file.

`adapter` formats `SemanticWorld` for a human explorer; `http` serves it on
loopback for the canvas. Neither writes.
"""

from world_explorer.adapter import WorldExplorerAdapter, open_world

__all__ = ["WorldExplorerAdapter", "open_world"]
