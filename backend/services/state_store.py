from abc import ABC, abstractmethod
from typing import Dict, Optional
from models.game import Room, AudioRecording

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

    @abstractmethod
    async def save_audio_recording(self, recording: AudioRecording) -> None:
        pass
    
    @abstractmethod
    async def get_audio_recording(self, recording_id: str) -> Optional[AudioRecording]:
        pass
    
    @abstractmethod
    async def delete_audio_recording(self, recording_id: str) -> None:
        pass
    
    @abstractmethod
    async def save_score(self, room_id: str, round_id: str, player_id: str, points: int, score_type: str) -> None:
        pass

class MemoryStateStore(StateStore):
    """In-memory implementation of state store"""
    
    def __init__(self):
        self._rooms: Dict[str, Room] = {}
        self._audio_recordings: Dict[str, AudioRecording] = {}
    
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
    
    async def save_audio_recording(self, recording: AudioRecording) -> None:
        self._audio_recordings[recording.id] = recording
    
    async def get_audio_recording(self, recording_id: str) -> Optional[AudioRecording]:
        return self._audio_recordings.get(recording_id)
    
    async def delete_audio_recording(self, recording_id: str) -> None:
        self._audio_recordings.pop(recording_id, None)
    
    async def save_score(self, room_id: str, round_id: str, player_id: str, points: int, score_type: str) -> None:
        """Save a score entry (memory store - no persistent storage)"""
        # In memory store, scores are already stored in Player objects
        # This method exists for compatibility with database store
        pass

# Global instance
state_store = MemoryStateStore()