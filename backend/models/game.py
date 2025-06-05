from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from enum import Enum
import uuid
from datetime import datetime

class GameMode(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"

class VoteType(str, Enum):
    FOUR_CHOICE = "4choice"
    EIGHT_CHOICE = "8choice"

class SpeakerOrder(str, Enum):
    RANDOM = "random"
    SEQUENTIAL = "sequential"

class GamePhase(str, Enum):
    WAITING = "waiting"
    IN_ROUND = "in_round"
    RESULT = "result"
    CLOSED = "closed"

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    score: int = 0
    is_host: bool = False
    is_connected: bool = True
    joined_at: datetime = Field(default_factory=datetime.now)

class RoomConfig(BaseModel):
    mode: GameMode = GameMode.BASIC
    vote_type: VoteType = VoteType.FOUR_CHOICE
    speaker_order: SpeakerOrder = SpeakerOrder.SEQUENTIAL
    vote_timeout: int = 30  # seconds
    
    class Config:
        use_enum_values = True

class Round(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phrase: str
    emotion_id: str
    speaker_id: str
    votes: Dict[str, str] = Field(default_factory=dict)  # player_id -> emotion_id
    is_completed: bool = False
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

class Room(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    players: Dict[str, Player] = Field(default_factory=dict)
    config: RoomConfig = Field(default_factory=RoomConfig)
    phase: GamePhase = GamePhase.WAITING
    current_round: Optional[Round] = None
    round_history: List[Round] = Field(default_factory=list)
    current_speaker_index: int = 0
    host_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    def get_speaker_order(self) -> List[str]:
        """Get ordered list of player IDs for speaking"""
        player_ids = list(self.players.keys())
        if self.config.speaker_order == SpeakerOrder.RANDOM:
            import random
            random.shuffle(player_ids)
        return player_ids
    
    def get_current_speaker(self) -> Optional[Player]:
        """Get current speaker"""
        speaker_order = self.get_speaker_order()
        if not speaker_order:
            return None
        speaker_id = speaker_order[self.current_speaker_index % len(speaker_order)]
        return self.players.get(speaker_id)

# API Request/Response models
class CreateRoomRequest(BaseModel):
    mode: GameMode = GameMode.BASIC
    vote_type: VoteType = VoteType.FOUR_CHOICE
    speaker_order: SpeakerOrder = SpeakerOrder.SEQUENTIAL

class CreateRoomResponse(BaseModel):
    room_id: str
    host_token: str

class JoinRoomRequest(BaseModel):
    room_id: str
    player_name: str

class RoomState(BaseModel):
    room_id: str
    players: List[str]  # player names
    phase: GamePhase
    config: RoomConfig
    current_speaker: Optional[str] = None  # player name

class VoteRequest(BaseModel):
    round_id: str
    emotion_id: str

class RoundResult(BaseModel):
    round_id: str
    correct_emotion: str
    speaker_name: str
    scores: Dict[str, int]  # player_name -> score

class ErrorResponse(BaseModel):
    code: str
    message: str