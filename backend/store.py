"""In-memory state store."""

from typing import Dict, Any

# Global dictionary mapping room_id to its state and host token
rooms: Dict[str, Dict[str, Any]] = {}
