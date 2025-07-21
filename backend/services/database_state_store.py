"""
Database-backed StateStore implementation
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from models.game import Room, RoomConfig, Player, Round as RoundData
from models import AudioRecording
from models.database import (
    ChatSession, RoomParticipant, Round, Recording,
    Mode, EmotionType
)
from services.state_store import StateStore
from services.database_service import DatabaseService


class DatabaseStateStore(StateStore):
    """Database-backed state store implementation"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    async def create_room(self, room: Room) -> None:
        """Create a new room in the database"""
        async with self.db.get_session() as session:
            # Check if mode exists, create if not
            mode_result = await session.execute(
                select(Mode).where(Mode.name == room.config.mode)
            )
            mode = mode_result.scalar_one_or_none()
            
            if not mode:
                mode = Mode(
                    name=room.config.mode,
                    description=f"{room.config.mode} mode"
                )
                session.add(mode)
                await session.flush()
            
            # Create chat session
            chat_session = ChatSession(
                id=room.id,
                room_code=room.room_code,
                mode_id=mode.id,
                max_players=room.config.max_players,
                status="waiting"
            )
            session.add(chat_session)
            
            # Create room participants
            for player in room.players.values():
                participant = RoomParticipant(
                    chat_session_id=room.id,
                    session_id=player.id,
                    player_name=player.name,
                    is_host=(player.id == room.host_id)
                )
                session.add(participant)
            
            await session.commit()
    
    async def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room from the database"""
        async with self.db.get_session() as session:
            # Get chat session with all related data
            result = await session.execute(
                select(ChatSession)
                .options(
                    selectinload(ChatSession.mode),
                    selectinload(ChatSession.participants),
                    selectinload(ChatSession.rounds).selectinload(Round.emotion)
                )
                .where(ChatSession.id == room_id)
            )
            chat_session = result.scalar_one_or_none()
            
            if not chat_session:
                return None
            
            # Reconstruct Room object
            config = RoomConfig(
                mode=chat_session.mode.name,
                max_players=chat_session.max_players,
                vote_timeout=30,  # Default, not stored in DB
                emotions=[]  # Will be loaded from emotion_types
            )
            
            # Load players
            players = {}
            host_id = None
            for participant in chat_session.participants:
                player = Player(
                    id=participant.session_id,
                    name=participant.player_name,
                    is_ready=True,  # Default, not stored
                    score=0  # Will be calculated from scores table
                )
                players[player.id] = player
                if participant.is_host:
                    host_id = player.id
            
            # Load rounds
            rounds = []
            for db_round in sorted(chat_session.rounds, key=lambda r: r.round_number):
                round_data = RoundData(
                    phrase=db_round.prompt_text,
                    emotion_id=db_round.emotion_id,
                    speaker_id=db_round.speaker_session_id,
                    votes={},  # Will be loaded from emotion_votes
                    audio_recording_id=None  # Will be loaded from recordings
                )
                rounds.append(round_data)
            
            # Create Room instance
            room = Room(
                id=chat_session.room_code,  # Room.id is the room_code
                players=players,
                config=config,
                phase=chat_session.status,  # Map status to phase
                current_round=rounds[-1] if rounds else None,
                round_history=rounds,
                created_at=chat_session.created_at
            )
            
            return room
    
    async def update_room(self, room: Room) -> None:
        """Update a room in the database"""
        async with self.db.get_session() as session:
            # Update chat session
            result = await session.execute(
                select(ChatSession).where(ChatSession.id == room.id)
            )
            chat_session = result.scalar_one_or_none()
            
            if not chat_session:
                raise ValueError(f"Room {room.id} not found")
            
            chat_session.status = room.state
            if room.state == "finished":
                chat_session.finished_at = datetime.now(timezone.utc)
            
            # Update participants
            existing_participants = await session.execute(
                select(RoomParticipant).where(RoomParticipant.chat_session_id == room.id)
            )
            existing_map = {p.session_id: p for p in existing_participants.scalars()}
            
            # Add new players
            for player_id, player in room.players.items():
                if player_id not in existing_map:
                    participant = RoomParticipant(
                        chat_session_id=room.id,
                        session_id=player.id,
                        player_name=player.name,
                        is_host=(player.id == room.host_id)
                    )
                    session.add(participant)
                else:
                    # Update existing participant
                    existing_map[player_id].is_host = (player.id == room.host_id)
            
            # Remove players no longer in room
            for session_id, participant in existing_map.items():
                if session_id not in room.players:
                    await session.delete(participant)
            
            # Update rounds (only add new ones)
            existing_rounds = await session.execute(
                select(Round).where(Round.chat_session_id == room.id)
            )
            existing_round_numbers = {r.round_number for r in existing_rounds.scalars()}
            
            for round_data in room.rounds:
                if round_data.round_number not in existing_round_numbers:
                    # Get emotion type
                    emotion_result = await session.execute(
                        select(EmotionType).where(EmotionType.name_ja == round_data.emotion)
                    )
                    emotion = emotion_result.scalar_one_or_none()
                    
                    if not emotion:
                        # Create emotion type if not exists
                        emotion = EmotionType(
                            id=round_data.emotion.lower(),
                            name_ja=round_data.emotion,
                            name_en=round_data.emotion.lower()
                        )
                        session.add(emotion)
                        await session.flush()
                    
                    db_round = Round(
                        chat_session_id=room.id,
                        speaker_session_id=round_data.speaker_id,
                        prompt_text=round_data.phrase,
                        emotion_id=emotion.id,
                        round_number=round_data.round_number
                    )
                    session.add(db_round)
            
            await session.commit()
    
    async def delete_room(self, room_id: str) -> None:
        """Delete a room from the database"""
        async with self.db.get_session() as session:
            # Cascade delete will handle related records
            await session.execute(
                delete(ChatSession).where(ChatSession.id == room_id)
            )
            await session.commit()
    
    async def list_rooms(self) -> Dict[str, Room]:
        """List all rooms from the database"""
        rooms = {}
        async with self.db.get_session() as session:
            result = await session.execute(
                select(ChatSession).where(ChatSession.status != "finished")
            )
            chat_sessions = result.scalars().all()
            
            for chat_session in chat_sessions:
                room = await self.get_room(chat_session.id)
                if room:
                    rooms[room.id] = room
        
        return rooms
    
    async def save_audio_recording(self, recording: AudioRecording) -> None:
        """Save an audio recording to the database"""
        async with self.db.get_session() as session:
            # Find the round this recording belongs to
            round_result = await session.execute(
                select(Round).where(
                    Round.chat_session_id == recording.room_id,
                    Round.round_number == recording.round_number
                )
            )
            db_round = round_result.scalar_one_or_none()
            
            db_recording = Recording(
                id=recording.id,
                round_id=db_round.id if db_round else None,
                session_id=recording.player_id,
                audio_url=recording.file_path,
                duration=recording.duration
            )
            session.add(db_recording)
            await session.commit()
    
    async def get_audio_recording(self, recording_id: str) -> Optional[AudioRecording]:
        """Get an audio recording from the database"""
        async with self.db.get_session() as session:
            result = await session.execute(
                select(Recording)
                .options(selectinload(Recording.round))
                .where(Recording.id == recording_id)
            )
            db_recording = result.scalar_one_or_none()
            
            if not db_recording:
                return None
            
            recording = AudioRecording(
                id=db_recording.id,
                room_id=db_recording.round.chat_session_id if db_recording.round else "",
                player_id=db_recording.session_id,
                round_number=db_recording.round.round_number if db_recording.round else 0,
                emotion="",  # Not stored in recording
                file_path=db_recording.audio_url,
                created_at=db_recording.created_at,
                duration=db_recording.duration or 0
            )
            
            return recording
    
    async def delete_audio_recording(self, recording_id: str) -> None:
        """Delete an audio recording from the database"""
        async with self.db.get_session() as session:
            await session.execute(
                delete(Recording).where(Recording.id == recording_id)
            )
            await session.commit()