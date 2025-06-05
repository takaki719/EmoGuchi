"""In-memory state store module."""

from typing import Dict, Any


class StateStore:
    """Simple in-memory store for runtime game state."""

    def __init__(self) -> None:
        # Mapping of room_id to its state and host token
        self.rooms: Dict[str, Dict[str, Any]] = {}


# Singleton instance used by the application
store = StateStore()

__all__ = ["store"]
