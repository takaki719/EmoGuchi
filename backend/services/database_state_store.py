"""
Database-backed StateStore implementation
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
import logging

from models.game import Room, RoomConfig, Player, Round as RoundData
from models import AudioRecording
from models.database import (
    ChatSession, RoomParticipant, Round, Recording,
    Mode, EmotionType
)
from services.state_store import StateStore
from services.database_service import DatabaseService
from config import settings

logger = logging.getLogger(__name__)


class DatabaseStateStore(StateStore):
    """Database-backed state store implementation"""
    
    def __init__(self, db_service: DatabaseService):
        self.db = db_service
    
    def _map_phase_to_status(self, phase: str) -> str:
        """Map GamePhase to ChatSession status"""
        phase_mapping = {
            "waiting": "waiting",
            "in_round": "playing", 
            "result": "playing",
            "closed": "finished"
        }
        return phase_mapping.get(phase, "waiting")
    
    def _map_status_to_phase(self, status: str) -> str:
        """Map ChatSession status to GamePhase"""
        status_mapping = {
            "waiting": "waiting",
            "playing": "in_round",  # Default to in_round for playing
            "finished": "closed"
        }
        return status_mapping.get(status, "waiting")
    
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
                room_code=room.id,  # Use room.id as room_code
                mode_id=mode.id,
                max_players=settings.MAX_PLAYERS_PER_ROOM,
                status="waiting"
            )
            session.add(chat_session)
            
            # Create room participants
            for player in room.players.values():
                participant = RoomParticipant(
                    chat_session_id=room.id,
                    session_id=player.id,
                    player_name=player.name,
                    is_host=player.is_host
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
                vote_timeout=30  # Default, not stored in DB
            )
            
            # Load players
            players = {}
            for participant in chat_session.participants:
                player = Player(
                    id=participant.session_id,
                    name=participant.player_name,
                    is_host=participant.is_host,
                    score=0  # Will be calculated from scores table
                )
                players[player.id] = player
            
            # Load rounds
            rounds = []
            current_round = None
            for db_round in sorted(chat_session.rounds, key=lambda r: r.round_number):
                round_data = RoundData(
                    id=db_round.id,  # Use database ID
                    phrase=db_round.prompt_text,
                    emotion_id=db_round.emotion_id,
                    speaker_id=db_round.speaker_session_id,
                    votes={},  # Will be loaded from emotion_votes
                    audio_recording_id=None,  # Will be loaded from recordings
                    is_completed=False  # Assume all database rounds are completed for now
                )
                rounds.append(round_data)
            
            # Determine current_round based on room phase
            # If room is "in_round", the last round is the current active round
            if self._map_status_to_phase(chat_session.status) == "in_round" and rounds:
                current_round = rounds[-1]
                current_round.is_completed = False  # This is the active round
                rounds = rounds[:-1]  # Remove from history since it's current
            
            # Create Room instance
            room = Room(
                id=chat_session.room_code,  # Room.id is the room_code
                players=players,
                config=config,
                phase=self._map_status_to_phase(chat_session.status),  # Map status to phase
                current_round=current_round,
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
            
            chat_session.status = self._map_phase_to_status(room.phase)
            if room.phase == "closed":
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
                        is_host=player.is_host
                    )
                    session.add(participant)
                else:
                    # Update existing participant
                    existing_map[player_id].is_host = player.is_host
            
            # Remove players no longer in room
            for session_id, participant in existing_map.items():
                if session_id not in room.players:
                    await session.delete(participant)
            
            # Update rounds (both current_round and round_history)
            existing_rounds = await session.execute(
                select(Round).where(Round.chat_session_id == room.id)
            )
            existing_round_ids = {r.id for r in existing_rounds.scalars()}
            
            # Handle current active round (not yet in history)
            rounds_to_save = list(room.round_history)
            if room.current_round and not room.current_round.is_completed:
                # Add current round to the list to be saved
                rounds_to_save.append(room.current_round)
            
            for i, round_data in enumerate(rounds_to_save):
                if round_data.id not in existing_round_ids:
                    # Get emotion type - use emotion_id directly
                    emotion_result = await session.execute(
                        select(EmotionType).where(EmotionType.id == round_data.emotion_id)
                    )
                    emotion = emotion_result.scalar_one_or_none()
                    
                    if not emotion:
                        # Create emotion type if not exists
                        emotion = EmotionType(
                            id=round_data.emotion_id,
                            name_ja=round_data.emotion_id,  # Fallback
                            name_en=round_data.emotion_id
                        )
                        session.add(emotion)
                        await session.flush()
                    
                    db_round = Round(
                        id=round_data.id,  # Use the same ID
                        chat_session_id=room.id,
                        speaker_session_id=round_data.speaker_id,
                        prompt_text=round_data.phrase,
                        emotion_id=round_data.emotion_id,
                        round_number=i + 1  # Calculate based on order
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
            # Find the round this recording belongs to using round_id directly
            round_result = await session.execute(
                select(Round).where(Round.id == recording.round_id)
            )
            db_round = round_result.scalar_one_or_none()
            
            # Save audio data to storage first
            from services.storage_service import get_storage_service
            storage_service = get_storage_service()
            audio_url = storage_service.save_audio(
                recording.audio_data, 
                getattr(recording, 'session_id', 'unknown'),
                recording.round_id
            )
            
            db_recording = Recording(
                id=recording.id,
                round_id=db_round.id if db_round else recording.round_id,
                session_id=getattr(recording, 'speaker_id', getattr(recording, 'session_id', 'unknown')),
                audio_url=audio_url,
                duration=getattr(recording, 'duration_seconds', None)
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
            
            # Audio data loading not implemented yet - using empty bytes
            # TODO: Implement audio data loading from storage when needed
            audio_data = b""
            
            recording = AudioRecording(
                id=db_recording.id,
                round_id=db_recording.round_id,
                speaker_id=db_recording.session_id,
                audio_data=audio_data,
                emotion_acted="",  # Would need to be retrieved from round
                duration_seconds=db_recording.duration,
                created_at=db_recording.created_at
            )
            
            return recording
    
    async def delete_audio_recording(self, recording_id: str) -> None:
        """Delete an audio recording from the database"""
        async with self.db.get_session() as session:
            await session.execute(
                delete(Recording).where(Recording.id == recording_id)
            )
            await session.commit()
    
    async def save_score(self, room_id: str, round_id: str, player_id: str, points: int, score_type: str) -> None:
        """Save a score entry to the database"""
        from models.database import Score
        
        async with self.db.get_session() as session:
            score = Score(
                session_id=player_id,
                round_id=round_id,
                points=points,
                score_type=score_type
            )
            session.add(score)
            await session.commit()
            logger.info(f"Saved score: player={player_id}, round={round_id}, points={points}, type={score_type}")