from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from enum import Enum
import uuid
import random
from datetime import datetime, timezone

class GameMode(str, Enum):
    BASIC = "basic"
    ADVANCED = "advanced"
    WHEEL = "wheel"

class VoteType(str, Enum):
    FOUR_CHOICE = "4choice"
    EIGHT_CHOICE = "8choice"
    WHEEL = "wheel"
    
    @classmethod
    def get_default_for_mode(cls, mode: 'GameMode') -> 'VoteType':
        """Get default vote type for a given game mode"""
        if mode == GameMode.ADVANCED:
            return cls.EIGHT_CHOICE
        elif mode == GameMode.WHEEL:
            return cls.WHEEL
        return cls.FOUR_CHOICE

class SpeakerOrder(str, Enum):
    RANDOM = "random"
    SEQUENTIAL = "sequential"

class GamePhase(str, Enum):
    WAITING = "waiting"
    IN_ROUND = "in_round"
    RESULT = "result"
    CLOSED = "closed"

def generate_room_id() -> str:
    """Generate a user-friendly room ID using word combinations"""
    adjectives = [
        "赤い", "青い", "緑の", "黄色い", "白い", "黒い", "大きな", "小さな",
        "明るい", "暗い", "速い", "遅い", "新しい", "古い", "強い", "弱い"
    ]
    
    nouns = [
        "わたる", "けいいち", "ひろひこ", "つかさ", "たかまさ", "こうせい", "けいた", "いっせい",
        "けんたろう", "れん", "ともかず", "こうき", "あつや", "こうた", "しゅうへい", "ゆうじ", "アンミンヒョン",
        "ももちゃん",
    ]
    
    # Generate format: adjective-noun-number
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    number = random.randint(100, 999)
    
    return f"{adjective}{noun}{number}"

class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    score: int = 0
    is_host: bool = False
    is_connected: bool = True
    mac_address: Optional[str] = None
    joined_at: datetime = Field(default_factory=datetime.now)

class RoomConfig(BaseModel):
    mode: GameMode = GameMode.BASIC
    vote_type: VoteType = VoteType.FOUR_CHOICE
    speaker_order: SpeakerOrder = SpeakerOrder.SEQUENTIAL
    vote_timeout: int = 30  # seconds
    max_rounds: int = 1  # Number of cycles to play
    hard_mode: bool = False  # Enable voice processing for difficulty
    
    class Config:
        use_enum_values = True

class AudioRecording(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    round_id: str
    speaker_id: str
    audio_data: bytes
    emotion_acted: str
    duration_seconds: Optional[float] = None
    created_at: datetime = Field(default_factory=datetime.now)

class Round(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    phrase: str
    emotion_id: str
    speaker_id: str
    votes: Dict[str, str] = Field(default_factory=dict)  # player_id -> emotion_id
    audio_recording_id: Optional[str] = None
    is_completed: bool = False
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    # ラウンド開始時の参加者スナップショット（投票権管理用）
    eligible_voters: List[str] = Field(default_factory=list)  # player_ids who can vote
    # 投票タイムアウト関連
    voting_started_at: Optional[datetime] = None  # 投票開始時刻
    vote_timeout_seconds: int = 30  # 投票制限時間（秒）

class Room(BaseModel):
    id: str = Field(default_factory=generate_room_id)
    players: Dict[str, Player] = Field(default_factory=dict)
    config: RoomConfig = Field(default_factory=RoomConfig)
    phase: GamePhase = GamePhase.WAITING
    current_round: Optional[Round] = None
    round_history: List[Round] = Field(default_factory=list)
    current_speaker_index: int = 0
    speaker_order_cache: Optional[List[str]] = None  # Cached speaker order for current cycle
    host_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.now)
    
    def get_speaker_order(self) -> List[str]:
        """Get ordered list of player IDs for speaking"""
        # Check if cached order is still valid
        connected_player_ids = {pid for pid, player in self.players.items() if player.is_connected}
        if (self.speaker_order_cache and 
            set(self.speaker_order_cache) == connected_player_ids):
            return self.speaker_order_cache
        
        # Generate new order - only include connected players
        player_ids = [pid for pid, player in self.players.items() if player.is_connected]
        if self.config.speaker_order == SpeakerOrder.RANDOM:
            import random
            random.shuffle(player_ids)
        
        # Cache the order
        self.speaker_order_cache = player_ids
        return player_ids
    
    def reset_speaker_order(self):
        """Reset speaker order cache for a new cycle"""
        self.speaker_order_cache = None
    
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
    max_rounds: int = 1  # Number of cycles to play
    hard_mode: bool = False  # Enable voice processing for difficulty
    room_id: Optional[str] = None  # Custom room ID/passphrase

class CreateRoomResponse(BaseModel):
    roomId: str
    hostToken: str
    isExistingRoom: bool = False

class JoinRoomRequest(BaseModel):
    room_id: str
    player_name: str

class RoomState(BaseModel):
    roomId: str
    players: List[str]  # player names
    phase: GamePhase
    config: RoomConfig
    currentSpeaker: Optional[str] = None  # player name

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

class AudioRecordingV2(BaseModel):
    """Audio recording data model for state store (deprecated)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    round_id: str
    audio_data: bytes
    audio_url: Optional[str] = None
    is_processed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))