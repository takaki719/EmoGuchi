from abc import ABC, abstractmethod
from typing import Dict, Optional
from models.game import Room

class StateStore(ABC):
    """Abstract state store for room management"""
    
    @abstractmethod
    async def create_room(self, room: Room) -> None:
        pass
    
    @abstractmethod
    async def get_room(self, room_id: str) -> Optional[Room]:
        pass
    
    @abstractmethod
    async def update_room(self, room: Room) -> None:
        pass
    
    @abstractmethod
    async def delete_room(self, room_id: str) -> None:
        pass
    
    @abstractmethod
    async def list_rooms(self) -> Dict[str, Room]:
        pass

class MemoryStateStore(StateStore):
    """In-memory implementation of state store"""
    
    def __init__(self):
        self._rooms: Dict[str, Room] = {}
    
    async def create_room(self, room: Room) -> None:
        self._rooms[room.id] = room
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        return self._rooms.get(room_id)
    
    async def update_room(self, room: Room) -> None:
        self._rooms[room.id] = room
    
    async def delete_room(self, room_id: str) -> None:
        self._rooms.pop(room_id, None)
    
    async def list_rooms(self) -> Dict[str, Room]:
        return self._rooms.copy()

# Global instance
state_store = MemoryStateStore()