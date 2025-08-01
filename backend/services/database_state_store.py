"""
Database-backed StateStore implementation
"""

from typing import Dict, Optional
from datetime import datetime, timezone
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
import logging
import uuid

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
                status="waiting",
                host_token=room.host_token,
                vote_type=room.config.vote_type,
                speaker_order=room.config.speaker_order,
                max_rounds=room.config.max_rounds,
                hard_mode=room.config.hard_mode,
                vote_timeout=room.config.vote_timeout
            )
            session.add(chat_session)
            await session.flush()  # Get the chat_session.id
            
            # Create room participants with autoflush disabled
            with session.no_autoflush:
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
            # Get the latest active chat session for this room_code
            result = await session.execute(
                select(ChatSession)
                .options(
                    selectinload(ChatSession.mode),
                    selectinload(ChatSession.participants),
                    selectinload(ChatSession.rounds).selectinload(Round.emotion)
                )
                .where(ChatSession.room_code == room_id)
                .where(ChatSession.status != "finished")
                .order_by(ChatSession.created_at.desc())  # Get the latest session
            )
            chat_session = result.scalars().first()
            
            if not chat_session:
                return None
            
            # Reconstruct Room object
            config = RoomConfig(
                mode=chat_session.mode.name,
                vote_type=chat_session.vote_type,
                speaker_order=chat_session.speaker_order,
                max_rounds=chat_session.max_rounds,
                hard_mode=chat_session.hard_mode,
                vote_timeout=chat_session.vote_timeout
            )
            
            # Load players and calculate their scores from the current session only
            players = {}
            for participant in chat_session.participants:
                # Calculate total score for this player from Score table
                # BUT only for rounds that belong to the current chat session
                from models.database import Score
                
                # Get round IDs that belong to the current session
                round_ids_subquery = select(Round.id).where(Round.chat_session_id == chat_session.id)
                
                # Calculate sum of points for this player in current session rounds
                score_result = await session.execute(
                    select(func.sum(Score.points))
                    .where(Score.session_id == participant.session_id)
                    .where(Score.round_id.in_(round_ids_subquery))
                )
                session_score = score_result.scalar() or 0
                
                player = Player(
                    id=participant.session_id,
                    name=participant.player_name,
                    is_host=participant.is_host,
                    score=session_score  # Calculate from current session scores only
                )
                players[player.id] = player
                logger.info(f"🎯 Loaded player {player.name} with session score: {session_score} (session: {chat_session.id})")
            
            # Load rounds
            rounds = []
            current_round = None
            for db_round in sorted(chat_session.rounds, key=lambda r: r.round_number):
                # Parse eligible_voters from JSON string
                import json
                eligible_voters = []
                if db_round.eligible_voters:
                    try:
                        eligible_voters = json.loads(db_round.eligible_voters)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse eligible_voters for round {db_round.id}")
                
                # Ensure voting_started_at has timezone info
                voting_started_at = db_round.voting_started_at
                if voting_started_at and voting_started_at.tzinfo is None:
                    # If offset-naive, assume it's UTC
                    voting_started_at = voting_started_at.replace(tzinfo=timezone.utc)
                
                # Load votes from EmotionVote table
                from models.database import EmotionVote
                vote_results = await session.execute(
                    select(EmotionVote)
                    .where(EmotionVote.round_id == db_round.id)
                )
                votes = {}
                for vote in vote_results.scalars():
                    votes[vote.voter_session_id] = vote.selected_emotion_id
                
                round_data = RoundData(
                    id=db_round.id,  # Use database ID
                    phrase=db_round.prompt_text,
                    emotion_id=db_round.emotion_id,
                    speaker_id=db_round.speaker_session_id,
                    votes=votes,  # Loaded from emotion_votes
                    audio_recording_id=None,  # Will be loaded from recordings
                    is_completed=False,  # Assume all database rounds are completed for now
                    eligible_voters=eligible_voters,
                    voting_started_at=voting_started_at,
                    vote_timeout_seconds=db_round.vote_timeout_seconds or 30
                )
                logger.info(f"⏰ Loaded round {db_round.id} with voting_started_at: {db_round.voting_started_at}")
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
                current_speaker_index=chat_session.current_speaker_index or 0,
                host_token=chat_session.host_token or str(uuid.uuid4()),  # Fallback for existing records
                created_at=chat_session.created_at
            )
            
            return room
    
    async def update_room(self, room: Room) -> None:
        """Update a room in the database"""
        async with self.db.get_session() as session:
            # Update the latest active chat session for this room_code
            result = await session.execute(
                select(ChatSession)
                .where(ChatSession.room_code == room.id)
                .where(ChatSession.status != "finished")
                .order_by(ChatSession.created_at.desc())
            )
            chat_session = result.scalars().first()
            
            if not chat_session:
                raise ValueError(f"Room {room.id} not found")
            
            chat_session.status = self._map_phase_to_status(room.phase)
            chat_session.current_speaker_index = room.current_speaker_index  # Update speaker index
            chat_session.host_token = room.host_token  # Update host token
            # Update room configuration
            chat_session.vote_type = room.config.vote_type
            chat_session.speaker_order = room.config.speaker_order
            chat_session.max_rounds = room.config.max_rounds
            chat_session.hard_mode = room.config.hard_mode
            chat_session.vote_timeout = room.config.vote_timeout
            if room.phase == "closed":
                chat_session.finished_at = datetime.now(timezone.utc)
            
            # Update participants with autoflush disabled
            with session.no_autoflush:
                existing_participants = await session.execute(
                    select(RoomParticipant).where(RoomParticipant.chat_session_id == chat_session.id)
                )
                existing_map = {p.session_id: p for p in existing_participants.scalars()}
                
                # Add new players
                for player_id, player in room.players.items():
                    if player_id not in existing_map:
                        participant = RoomParticipant(
                            chat_session_id=chat_session.id,  # Use correct ChatSession.id
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
            
            # Update rounds (both current_round and round_history) with autoflush disabled
            with session.no_autoflush:
                # Get the actual ChatSession.id for this room_code
                existing_rounds = await session.execute(
                    select(Round).where(Round.chat_session_id == chat_session.id)
                )
                existing_round_ids = {r.id for r in existing_rounds.scalars()}
                
                # Handle current active round (not yet in history)
                rounds_to_save = list(room.round_history)
                if room.current_round and not room.current_round.is_completed:
                    # Add current round to the list to be saved
                    rounds_to_save.append(room.current_round)
                
            for i, round_data in enumerate(rounds_to_save):
                if round_data.id not in existing_round_ids:
                    # Create new round
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
                    
                    # Serialize eligible_voters to JSON string
                    import json
                    eligible_voters_json = json.dumps(round_data.eligible_voters) if round_data.eligible_voters else None
                    
                    db_round = Round(
                        id=round_data.id,  # Use the same ID
                        chat_session_id=chat_session.id,  # Use correct ChatSession.id
                        speaker_session_id=round_data.speaker_id,
                        prompt_text=round_data.phrase,
                        emotion_id=round_data.emotion_id,
                        round_number=i + 1,  # Calculate based on order
                        eligible_voters=eligible_voters_json,
                        voting_started_at=round_data.voting_started_at,
                        vote_timeout_seconds=round_data.vote_timeout_seconds
                    )
                    session.add(db_round)
                else:
                    # Update existing round
                    existing_round_result = await session.execute(
                        select(Round).where(Round.id == round_data.id)
                    )
                    existing_round = existing_round_result.scalar_one_or_none()
                    
                    if existing_round:
                        # Update voting-related fields
                        import json
                        eligible_voters_json = json.dumps(round_data.eligible_voters) if round_data.eligible_voters else None
                        
                        existing_round.eligible_voters = eligible_voters_json
                        existing_round.voting_started_at = round_data.voting_started_at
                        existing_round.vote_timeout_seconds = round_data.vote_timeout_seconds
                        logger.info(f"⏰ Updated existing round {round_data.id} with voting_started_at: {round_data.voting_started_at}")
                
                # Save votes for this round
                if round_data.votes:
                    # Delete existing votes for this round
                    from models.database import EmotionVote
                    await session.execute(
                        delete(EmotionVote).where(EmotionVote.round_id == round_data.id)
                    )
                    
                    # Add new votes
                    for player_id, emotion_id in round_data.votes.items():
                        vote = EmotionVote(
                            round_id=round_data.id,
                            voter_session_id=player_id,
                            selected_emotion_id=emotion_id,
                            is_correct=(emotion_id == round_data.emotion_id)
                        )
                        session.add(vote)
                    
                    logger.info(f"💾 Saved {len(round_data.votes)} votes for round {round_data.id}")
            
            await session.commit()
    
    async def delete_room(self, room_id: str) -> None:
        """Delete a room from the database"""
        async with self.db.get_session() as session:
            # Delete all sessions for this room_code (cascade delete will handle related records)
            await session.execute(
                delete(ChatSession).where(ChatSession.room_code == room_id)
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
                room = await self.get_room(chat_session.room_code)  # Use room_code instead of id
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
    
    async def _end_current_session_and_create_new(self, old_room: Room, new_room: Room) -> None:
        """End current session and create new session for restart_game"""
        async with self.db.get_session() as session:
            # 1. End ALL active sessions for this room_code
            result = await session.execute(
                select(ChatSession)
                .where(ChatSession.room_code == old_room.id)
                .where(ChatSession.status != "finished")
            )
            active_sessions = result.scalars().all()
            
            for current_session in active_sessions:
                current_session.status = "finished"
                current_session.finished_at = datetime.now(timezone.utc)
                logger.info(f"🔄 Ended session {current_session.id}")
            
            logger.info(f"🔄 Ended {len(active_sessions)} active sessions for room_code {old_room.id}")
            
            # 2. Create new session with same room_code
            # Check if mode exists, create if not
            mode_result = await session.execute(
                select(Mode).where(Mode.name == new_room.config.mode)
            )
            mode = mode_result.scalar_one_or_none()
            
            if not mode:
                mode = Mode(
                    name=new_room.config.mode,
                    description=f"{new_room.config.mode} mode"
                )
                session.add(mode)
                await session.flush()
            
            # Create new chat session with same room_code but new ID
            new_session = ChatSession(
                # id will be auto-generated (new UUID)
                room_code=new_room.id,  # Same room_code for Socket.IO compatibility
                mode_id=mode.id,
                max_players=settings.MAX_PLAYERS_PER_ROOM,
                status="waiting",
                host_token=new_room.host_token,
                vote_type=new_room.config.vote_type,
                speaker_order=new_room.config.speaker_order,
                max_rounds=new_room.config.max_rounds,
                hard_mode=new_room.config.hard_mode,
                vote_timeout=new_room.config.vote_timeout
            )
            session.add(new_session)
            await session.flush()  # Get the new session ID
            
            logger.info(f"🔄 Created new session {new_session.id} for room_code {new_room.id}")
            
            # 3. Create room participants for new session with autoflush disabled
            with session.no_autoflush:
                for player in new_room.players.values():
                    participant = RoomParticipant(
                        chat_session_id=new_session.id,  # New session ID
                        session_id=player.id,
                        player_name=player.name,
                        is_host=player.is_host
                    )
                    session.add(participant)
            
            await session.commit()
            logger.info(f"🔄 Successfully created new game session")