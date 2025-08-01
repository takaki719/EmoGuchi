import socketio
from typing import Dict, Any
from datetime import datetime, timezone
from models.game import Player, GamePhase, Round, AudioRecording
from logging import getLogger

logger = getLogger(__name__)

def get_state_store():
    """Dynamically get the state store to avoid circular imports"""
    import services
    if services.state_store is None:
        # Fallback to the global instance if not properly initialized
        from services.state_store import state_store as global_state_store
        logger.warning("Using fallback global state_store")
        return global_state_store
    logger.info(f"Getting state_store: {services.state_store}")
    logger.info(f"State store type: {type(services.state_store)}")
    return services.state_store

class GameSocketEvents:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        # 初期化時にsioがNoneでないことを確認
        if self.sio is None:
            raise ValueError("SocketIO server instance cannot be None")
        self.setup_events()
    
    def setup_events(self):
        """Register all socket event handlers"""
        
        # Capture self in local scope to avoid closure issues
        events_instance = self
        
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            await events_instance.sio.emit('connected', {'message': 'Connected to EMOGUCHI server'}, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
            # Handle player disconnection
            await events_instance._handle_player_disconnect(sid)
        
        @self.sio.event
        async def join_room(sid, data):
            """Handle player joining a room"""
            try:
                logger.info(f"join_room event received from {sid} with data: {data}")
                room_id = data.get('roomId')
                player_name = data.get('playerName')
                player_id = data.get('playerId')  # 永続化されたPlayer ID
                
                if not room_id or not player_name:
                    logger.error(f"Missing data - roomId: {room_id}, playerName: {player_name}")
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Missing roomId or playerName'
                    }, room=sid)
                    return
                
                state_store = get_state_store()
                logger.info(f"Searching for room: {room_id}")
                room = await state_store.get_room(room_id)
                logger.info(f"Room found: {room is not None}")
                
                if not room:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room not found'
                    }, room=sid)
                    return
                
                # Check if player already exists (by ID or name for backward compatibility)
                existing_player = None
                
                # First, try to find by player_id if provided
                if player_id:
                    existing_player = room.players.get(player_id)
                    if existing_player:
                        logger.info(f"Found existing player by ID: {player_id}")
                        # Update name if changed
                        existing_player.name = player_name
                
                # Fallback: check by name for backward compatibility
                if not existing_player:
                    for p in room.players.values():
                        if p.name == player_name:
                            existing_player = p
                            logger.info(f"Found existing player by name: {player_name}")
                            break
                
                if existing_player:
                    # Reconnect existing player
                    player = existing_player
                    player.is_connected = True
                    logger.info(f"Player {player.name} ({player.id}) reconnected to room {room_id}")
                else:
                    # Create new player with provided ID or generate new one
                    if player_id:
                        player = Player(id=player_id, name=player_name)
                    else:
                        player = Player(name=player_name)  # Auto-generate ID
                    
                    if not room.players:  # First player becomes host
                        player.is_host = True
                    room.players[player.id] = player
                
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Join socket room
                try:
                    await events_instance.sio.enter_room(sid, room_id)
                except Exception as e:
                    logger.error(f"Error joining socket room: {e}")
                
                # Store player-room mapping
                try:
                    await events_instance.sio.save_session(sid, {
                        'player_id': player.id,
                        'room_id': room_id
                    })
                except Exception as e:
                    logger.error(f"Error saving session: {e}")
                
                # Notify room about player
                if existing_player:
                    await events_instance.sio.emit('player_reconnected', {
                        'playerName': player.name,
                        'playerId': player.id
                    }, room=room_id)
                else:
                    await events_instance.sio.emit('player_joined', {
                        'playerName': player.name,
                        'playerId': player.id
                    }, room=room_id)
                
                # Send current room state
                # Include player scores in the room state
                players_data = [{'name': p.name, 'score': p.score} for p in room.players.values()]
                current_speaker = None
                
                if room.current_round and room.phase == GamePhase.IN_ROUND:
                    speaker = room.get_current_speaker()
                    if speaker:
                        current_speaker = speaker.name
                
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': players_data,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': current_speaker
                }, room=room_id)
                
            except Exception as e:
                logger.error(f"Error in join_room: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def start_round(sid, data):
            """Start a new round (host only)"""
            try:
                session = await events_instance.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                if not room_id or not player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                state_store = get_state_store()
                room = await state_store.get_room(room_id)
                if not room:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room not found'
                    }, room=sid)
                    return
                
                player = room.players.get(player_id)
                if not player or not player.is_host:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-403',
                        'message': 'Only host can start rounds'
                    }, room=sid)
                    return
                
                if room.phase != GamePhase.WAITING:
                    logger.warning(f"Room {room_id} is in phase {room.phase}, not WAITING. Refusing to start round.")
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-409',
                        'message': f'Room is not in waiting phase (current: {room.phase})'
                    }, room=sid)
                    return
                
                # Check minimum player count (need at least 2 players: 1 speaker + 1 listener)
                if len(room.players) < 2:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Need at least 2 players to start the game'
                    }, room=sid)
                    return
                
                # Generate phrase and emotion with LLM
                from services.llm_service import llm_service
                phrase, emotion_id = await llm_service.generate_phrase_with_emotion(room.config.mode, room.config.vote_type)
                
                # Get current speaker
                logger.info(f"🎤 START_ROUND: room.current_speaker_index BEFORE get_speaker_order = {room.current_speaker_index}")
                speaker_order = room.get_speaker_order()
                speaker = room.get_current_speaker()
                logger.info(f"🎤 Starting round - Speaker index: {room.current_speaker_index}, Speaker: {speaker.name if speaker else 'None'}")
                logger.info(f"🎤 Speaker order: {speaker_order}")
                logger.info(f"🎤 Speaker order length: {len(speaker_order)}")
                logger.info(f"🎤 All players: {[(pid, p.name, p.is_connected) for pid, p in room.players.items()]}")
                logger.info(f"🎤 Speaker calculation: speaker_order[{room.current_speaker_index} % {len(speaker_order)}] = {speaker_order[room.current_speaker_index % len(speaker_order)] if speaker_order else 'No order'}")
                
                if not speaker:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'No players available'
                    }, room=sid)
                    return
                
                # Create round with eligible voters snapshot
                # Only connected players at round start (excluding speaker) can vote
                eligible_voters = [
                    player_id for player_id, player in room.players.items()
                    if player.is_connected and player_id != speaker.id
                ]
                
                round_data = Round(
                    phrase=phrase,
                    emotion_id=emotion_id,
                    speaker_id=speaker.id,
                    eligible_voters=eligible_voters
                )
                
                logger.info(f"🎯 Round created with {len(eligible_voters)} eligible voters: {eligible_voters}")
                
                room.current_round = round_data
                room.phase = GamePhase.IN_ROUND
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Send updated room state to all players to sync phase first
                # Include player scores in the room state
                players_data = [{'name': p.name, 'score': p.score} for p in room.players.values()]
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': players_data,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': speaker.name
                }, room=room_id)
                
                # Generate voting choices for this round
                logger.info(f"🎯 Room config for voting: {room.config.dict()}")
                from models.emotion import get_emotion_choices_for_voting
                choice_data = []
                if room.config.vote_type != "wheel":
                    if room.config.vote_type == "8choice":
                        logger.info(f"🎯 Using 8-choice voting")
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, emotion_id, 8, room.config.vote_type)
                    else:
                        logger.info(f"🎯 Using 4-choice voting (vote_type: {room.config.vote_type})")
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, emotion_id, 4, room.config.vote_type)
                    
                    choice_data = [{"id": choice.id, "name": choice.name_ja} for choice in voting_choices]
                    logger.info(f"🎯 Generated {len(choice_data)} voting choices: {[c['name'] for c in choice_data]}")
                
                # Send round start to all players with voting choices
                await events_instance.sio.emit('round_start', {
                    'roundId': round_data.id,
                    'phrase': phrase,
                    'speakerName': speaker.name,
                    'votingChoices': choice_data
                }, room=room_id)
                
                # Send speaker-specific data (emotion) only to the speaker
                emotion_name = emotion_id  # fallback
                
                if room.config.vote_type == "wheel":
                    # For wheel mode, use 3-layer emotions
                    from models.emotion_3_layer import EMOTIONS_3_LAYER
                    emotion_data = EMOTIONS_3_LAYER.get(emotion_id)
                    if emotion_data:
                        emotion_name = emotion_data.name_ja  # 日本語のみ
                else:
                    # For traditional modes
                    from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
                    emotions_dict = BASIC_EMOTIONS if room.config.mode == "basic" else ADVANCED_EMOTIONS
                    emotion_data = emotions_dict.get(emotion_id)
                    if emotion_data:
                        emotion_name = emotion_data.name_ja  # 日本語のみ
                
                # スピーカーに感情情報を送信（全ルームメンバーに送信し、フロントエンドで制御）
                await events_instance.sio.emit('speaker_emotion', {
                    'emotion': emotion_name,
                    'emotionId': emotion_id,
                    'speakerId': speaker.id  # スピーカーIDを追加してフロントエンドで判定
                }, room=room_id)
                
                logger.info(f"Round started in room {room_id}: {phrase} with emotion {emotion_name}")
                
            except Exception as e:
                logger.error(f"Error in start_round: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def audio_send(sid, data):
            """Handle audio data from speaker"""
            logger.info(f"🔥 audio_send event received from sid: {sid}")
            logger.info(f"🔥 audio_send data keys: {list(data.keys()) if isinstance(data, dict) else 'not dict'}")
            
            try:
                session = await events_instance.sio.get_session(sid)
                logger.info(f"🔥 Session data: {session}")
                
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                logger.info(f"🔥 Extracted room_id: {room_id}, player_id: {player_id}")
                
                if not room_id or not player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                state_store = get_state_store()
                logger.info(f"Getting state_store: {state_store}")
                logger.info(f"State store type: {type(state_store)}")
                room = await state_store.get_room(room_id)
                if not room or not room.current_round:
                    logger.error(f"🚨 audio_send: No active round - room exists: {room is not None}, current_round: {room.current_round if room else None}")
                    if room:
                        logger.error(f"🚨 audio_send: Room phase: {room.phase}, round_history length: {len(room.round_history)}")
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'No active round'
                    }, room=sid)
                    return
                
                # Verify that sender is the current speaker
                if room.current_round.speaker_id != player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-403',
                        'message': 'Only the speaker can send audio'
                    }, room=sid)
                    return
                
                # Create audio recording
                audio_data = data.get('audio')
                if not audio_data:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'No audio data provided'
                    }, room=sid)
                    return
                
                logger.info(f"Received audio data, type: {type(audio_data)}, size: {len(audio_data) if hasattr(audio_data, '__len__') else 'unknown'}")
                
                # Get emotion info
                from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
                emotion_acted = room.current_round.emotion_id
                emotion_name = emotion_acted
                
                for emotion_info in BASIC_EMOTIONS.values():
                    if emotion_info.id == emotion_acted:
                        emotion_name = emotion_info.name_ja
                        break
                else:
                    for emotion_info in ADVANCED_EMOTIONS.values():
                        if emotion_info.id == emotion_acted:
                            emotion_name = emotion_info.name_ja
                            break
                
                # Convert audio data to bytes if needed
                if isinstance(audio_data, (list, tuple)):
                    audio_bytes = bytes(audio_data)
                elif hasattr(audio_data, 'tobytes'):
                    audio_bytes = audio_data.tobytes()
                else:
                    audio_bytes = audio_data
                
                # Save audio recording
                recording = AudioRecording(
                    round_id=room.current_round.id,
                    speaker_id=player_id,
                    audio_data=audio_bytes,
                    emotion_acted=room.current_round.emotion_id
                )
                
                state_store = get_state_store()
                await state_store.save_audio_recording(recording)
                logger.info(f"Audio recording saved with ID: {recording.id}")
                
                # Update round with audio recording ID
                room.current_round.audio_recording_id = recording.id
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Apply voice processing if hard mode is enabled
                processed_audio = audio_data  # Default to original audio
                logger.info(f"🎯 Hard mode check: room.config.hard_mode = {room.config.hard_mode}")
                
                if room.config.hard_mode:
                    logger.info("🎯 Hard mode is ON - attempting voice processing")
                    try:
                        from services.voice_processing_service import voice_processing_service
                        logger.info(f"🎯 Voice processing service enabled: {voice_processing_service.is_enabled()}")
                        
                        if voice_processing_service.is_enabled():
                            # Select processing pattern based on emotion
                            processing_config = voice_processing_service.select_processing_pattern(
                                room.current_round.emotion_id
                            )
                            logger.info(f"🎯 Selected processing config: {processing_config.pattern.value}, pitch={processing_config.pitch}, tempo={processing_config.tempo}")
                            
                            # Process the audio
                            logger.info(f"🎯 Processing audio: input size={len(audio_bytes)} bytes")
                            processed_audio_bytes = voice_processing_service.process_audio(
                                audio_bytes, processing_config
                            )
                            
                            if processed_audio_bytes and processed_audio_bytes != audio_bytes:
                                # Convert back to format expected by frontend
                                if isinstance(audio_data, (list, tuple)):
                                    processed_audio = list(processed_audio_bytes)
                                else:
                                    processed_audio = processed_audio_bytes
                                
                                logger.info(f"🎯 ✅ Audio processed successfully with {processing_config.pattern.value}: "
                                          f"pitch={processing_config.pitch}, tempo={processing_config.tempo}, output size={len(processed_audio_bytes)}")
                            else:
                                logger.warning("🎯 ❌ Audio processing failed or returned same audio, using original audio")
                        else:
                            logger.warning("🎯 ❌ Voice processing service not available, using original audio")
                    except Exception as e:
                        logger.error(f"🎯 ❌ Voice processing error: {e}", exc_info=True)
                        # Continue with original audio if processing fails
                else:
                    logger.info("🎯 Hard mode is OFF - using original audio")
                
                # Broadcast audio to all other players in the room
                # Speaker gets original audio, listeners get processed audio (if hard mode)
                # Generate UTC timestamp for consistency
                utc_now = datetime.now(timezone.utc)
                
                await events_instance.sio.emit('audio_received', {
                    'audio': processed_audio,
                    'speaker_name': room.players[player_id].name,
                    'is_processed': room.config.hard_mode and processed_audio != audio_data,
                    'vote_timeout_seconds': room.config.vote_timeout,  # タイマー情報を追加
                    'voting_started_at': utc_now.isoformat()  # 開始時刻も送信
                }, room=room_id, skip_sid=sid)
                
                # Start voting timer after audio is broadcast
                room.current_round.voting_started_at = utc_now
                room.current_round.vote_timeout_seconds = room.config.vote_timeout
                
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Schedule timeout check
                import asyncio
                timeout_task = asyncio.create_task(events_instance._check_vote_timeout(room_id, room.current_round.id))
                logger.info(f"⏰ Timeout task created for round {room.current_round.id} in room {room_id}")
                
                logger.info(f"Audio received and broadcast from speaker {player_id} in room {room_id}, data size: {len(audio_bytes)}")
                logger.info(f"⏰ Vote timer started: {room.config.vote_timeout}s timeout")
                logger.info(f"⏰ voting_started_at set to: {room.current_round.voting_started_at}")
                logger.info(f"⏰ Current UTC time: {utc_now}")
                
            except Exception as e:
                logger.error(f"Error in audio_send: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def submit_vote(sid, data):
            """Submit vote for current round"""
            try:
                session = await events_instance.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                round_id = data.get('roundId')
                emotion_id = data.get('emotionId')
                
                if not room_id or not player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                state_store = get_state_store()
                room = await state_store.get_room(room_id)
                if not room or not room.current_round:
                    logger.error(f"🚨 submit_vote: No active round - room exists: {room is not None}, current_round: {room.current_round if room else None}")
                    if room:
                        logger.error(f"🚨 submit_vote: Room phase: {room.phase}, round_history length: {len(room.round_history)}")
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'No active round'
                    }, room=sid)
                    return
                
                if room.current_round.id != round_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Invalid round ID'
                    }, room=sid)
                    return
                
                # Don't allow speaker to vote
                if room.current_round.speaker_id == player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Speaker cannot vote'
                    }, room=sid)
                    return
                
                # Only allow eligible voters (those present at round start) to vote
                if player_id not in room.current_round.eligible_voters:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-403', 
                        'message': 'You joined after the round started and cannot vote'
                    }, room=sid)
                    return
                
                # Record vote
                room.current_round.votes[player_id] = emotion_id
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Send vote confirmation to the voter
                await events_instance.sio.emit('vote_confirmed', {
                    'roundId': round_id,
                    'emotionId': emotion_id,
                    'message': 'Vote recorded successfully'
                }, room=sid)
                
                # Simplified vote completion logic - count all currently connected eligible voters
                current_connected_eligible = [
                    voter_id for voter_id in room.current_round.eligible_voters
                    if voter_id in room.players and room.players[voter_id].is_connected
                ]
                
                votes_received = len(room.current_round.votes)
                total_eligible = len(room.current_round.eligible_voters)
                connected_eligible = len(current_connected_eligible)
                
                logger.info(f"🗳️ Vote completion check:")
                logger.info(f"🗳️   Original eligible voters: {room.current_round.eligible_voters}")
                logger.info(f"🗳️   Currently connected eligible: {current_connected_eligible}")
                logger.info(f"🗳️   Votes received: {votes_received}/{connected_eligible} connected ({total_eligible} original)")
                logger.info(f"🗳️   Actual votes: {room.current_round.votes}")
                
                # Complete round when all currently connected eligible voters have voted
                should_complete = votes_received >= connected_eligible and connected_eligible > 0
                logger.info(f"🗳️ Should complete: {should_complete} (votes_received={votes_received} >= connected_eligible={connected_eligible})")
                
                if should_complete:
                    logger.info(f"🎉 All connected eligible voters have voted, completing round in room {room_id}")
                    await events_instance._complete_round(room)
                else:
                    remaining = connected_eligible - votes_received
                    logger.info(f"⏳ Waiting for {remaining} more votes from connected eligible voters in room {room_id}")
                
                logger.info(f"Vote submitted by player {player_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in submit_vote: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def restart_game(sid, data):
            """Restart the game (host only)"""
            logger.info(f"🔄 restart_game event received from {sid} with data: {data}")
            try:
                session = await events_instance.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                if not room_id or not player_id:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                state_store = get_state_store()
                room = await state_store.get_room(room_id)
                if not room:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room not found'
                    }, room=sid)
                    return
                
                logger.info(f"🔄 Room loaded from DB for restart: {room.config.dict()}")
                
                # Double-check database directly
                try:
                    from services.database_service import DatabaseService
                    from models.database import ChatSession
                    from sqlalchemy import select
                    
                    db_service = DatabaseService()
                    await db_service.initialize()
                    async with db_service.get_session() as session:
                        result = await session.execute(select(ChatSession).where(ChatSession.room_code == room_id))
                        chat_session = result.scalar_one_or_none()
                        if chat_session:
                            logger.info(f"🔄 Direct DB check - max_rounds: {chat_session.max_rounds}, vote_type: {chat_session.vote_type}")
                except Exception as e:
                    logger.error(f"🔄 DB check failed: {e}")
                
                player = room.players.get(player_id)
                if not player or not player.is_host:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-403',
                        'message': 'Only host can restart the game'
                    }, room=sid)
                    return
                
                # Create new game session instead of resetting current one
                logger.info(f"🔄 Creating new game session for room {room_id}")
                logger.info(f"🔄 Current room config before restart: {room.config.dict()}")
                
                # Create new room with same config and players
                from models.game import Room, Player
                new_room = Room(
                    id=room_id,  # Same room ID for Socket.IO compatibility
                    config=room.config,  # Keep current config
                    players={},  # Will be populated below
                    phase=GamePhase.WAITING,
                    current_round=None,
                    round_history=[],
                    current_speaker_index=0
                )
                
                # Copy players with reset scores
                logger.info(f"🔄 Copying {len(room.players)} players to new session")
                for player in room.players.values():
                    new_player = Player(
                        id=player.id,  # Keep same player ID
                        name=player.name,
                        is_host=player.is_host,
                        score=0,  # Reset score
                        is_connected=player.is_connected
                    )
                    new_room.players[player.id] = new_player
                
                new_room.reset_speaker_order()  # Initialize speaker order for new game
                
                # End current session and create new one
                state_store = get_state_store()
                if hasattr(state_store, '_end_current_session_and_create_new'):
                    # Use special method for DatabaseStateStore
                    await state_store._end_current_session_and_create_new(room, new_room)
                else:
                    # Fallback for MemoryStateStore
                    await state_store.update_room(new_room)
                
                # Update reference for subsequent operations
                room = new_room
                
                # Send updated room state to all players
                # Include player scores in the room state (all 0 after restart)
                players_data = [{'name': p.name, 'score': p.score} for p in room.players.values()]
                room_state_data = {
                    'roomId': room.id,
                    'players': players_data,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': None
                }
                logger.info(f"🔄 Sending room_state after restart: {room_state_data}")
                await events_instance.sio.emit('room_state', room_state_data, room=room_id)
                
                logger.info(f"🔄 Game restarted in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in restart_game: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
    
    async def _complete_round(self, room):
        """Complete current round and calculate scores"""
        try:
            if not room.current_round:
                return
            
            round_data = room.current_round
            correct_emotion = round_data.emotion_id
            
            # Calculate scores based on game mode
            speaker = room.players[round_data.speaker_id]
            correct_votes = 0
            
            # Use traditional binary scoring for choice modes
            for player_id, voted_emotion in round_data.votes.items():
                player = room.players.get(player_id)
                if player:
                    old_score = player.score
                    if voted_emotion == correct_emotion:
                        # Listener gets point for correct guess
                        player.score += 1
                        correct_votes += 1
                        logger.info(f"Player {player.name} guessed correctly. Score: {old_score} -> {player.score}")
                    else:
                        logger.info(f"Player {player.name} guessed wrong. Score remains: {player.score}")
            
            # Speaker gets points based on how many guessed correctly
            old_speaker_score = speaker.score
            speaker.score += correct_votes
            logger.info(f"Speaker {speaker.name} got {correct_votes} correct votes. Score: {old_speaker_score} -> {speaker.score}")
            
            # Save individual scores to database
            await self._save_round_scores(room, round_data, correct_votes)
            
            # Check if game should end (reached max cycles) - BEFORE completing round
            # One cycle = all players speak once
            completed_rounds = len(room.round_history) + 1  # +1 for current round being completed
            total_players = len([p for p in room.players.values() if p.is_connected])
            completed_cycles = completed_rounds // total_players if total_players > 0 else 0
            is_game_complete = completed_cycles >= room.config.max_rounds
            
            logger.info(f"🔄 Round completion check: completed_rounds={completed_rounds}, total_players={total_players}, "
                       f"completed_cycles={completed_cycles}, max_rounds={room.config.max_rounds}, "
                       f"is_game_complete={is_game_complete}, current_speaker_index={room.current_speaker_index}")
            logger.info(f"🔄 Room config during completion check: {room.config.dict()}")
            
            # Mark round as completed
            round_data.is_completed = True
            room.round_history.append(round_data)
            room.current_round = None
            
            # Set phase based on game completion
            if is_game_complete:
                room.phase = GamePhase.RESULT  # Game over
            else:
                room.phase = GamePhase.WAITING  # Ready for next round
            
            # Move to next speaker
            speaker_order = room.get_speaker_order()
            logger.info(f"🔄 BEFORE index update: current_speaker_index={room.current_speaker_index}, speaker_order_length={len(speaker_order)}")
            
            next_speaker_index = (room.current_speaker_index + 1) % len(speaker_order)
            logger.info(f"🔄 CALCULATED next_speaker_index: {next_speaker_index}")
            
            # If we've wrapped around to 0, we're starting a new cycle
            if next_speaker_index == 0 and room.current_speaker_index != 0:
                new_cycle_num = (len(room.round_history) // len(speaker_order)) + 1
                logger.info(f"🔄 Starting new cycle #{new_cycle_num}, resetting speaker order")
                room.reset_speaker_order()
            
            logger.info(f"🔄 SETTING room.current_speaker_index to {next_speaker_index}")
            room.current_speaker_index = next_speaker_index
            logger.info(f"🔄 AFTER setting: room.current_speaker_index={room.current_speaker_index}")
            
            # Log next speaker info
            updated_speaker_order = room.get_speaker_order()
            next_speaker = room.get_current_speaker()
            logger.info(f"🎤 Round completed - Next speaker: index={room.current_speaker_index}, name={next_speaker.name if next_speaker else 'None'}")
            logger.info(f"🎤 Updated speaker order: {updated_speaker_order}")
            logger.info(f"🎤 Total rounds completed so far: {len(room.round_history)}")
            
            state_store = get_state_store()
            logger.info(f"🔄 BEFORE DB save: room.current_speaker_index={room.current_speaker_index}")
            await state_store.update_room(room)
            logger.info(f"🔄 AFTER DB save: room.current_speaker_index={room.current_speaker_index}")
            
            # Verify by re-fetching from DB
            saved_room = await state_store.get_room(room.id)
            if saved_room:
                logger.info(f"🔄 DB VERIFICATION: saved room current_speaker_index={saved_room.current_speaker_index}")
            else:
                logger.error(f"🔄 DB VERIFICATION: Could not retrieve room from DB")
            
            # Send results
            # Log all players with their IDs and scores for debugging
            logger.info(f"All players in room {room.id}:")
            for pid, player in room.players.items():
                logger.info(f"  - ID: {pid}, Name: {player.name}, Score: {player.score}")
            
            scores = {player.name: player.score for player in room.players.values()}
            
            # Log votes debugging info
            logger.info(f"Round votes in room {room.id}:")
            for pid, emotion in round_data.votes.items():
                player = room.players.get(pid)
                if player:
                    logger.info(f"  - Player {player.name} (ID: {pid}) voted: {emotion}")
                else:
                    logger.info(f"  - Unknown player (ID: {pid}) voted: {emotion}")
            
            # Get emotion name for display
            correct_emotion_name = correct_emotion  # fallback
            
            # For traditional modes
            from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
            
            # Try to find emotion name
            for emotion_info in BASIC_EMOTIONS.values():
                if emotion_info.id == correct_emotion:
                    correct_emotion_name = emotion_info.name_ja
                    break
            else:
                for emotion_info in ADVANCED_EMOTIONS.values():
                    if emotion_info.id == correct_emotion:
                        correct_emotion_name = emotion_info.name_ja
                        break
            
            result_data = {
                'round_id': round_data.id,
                'correct_emotion': correct_emotion_name,
                'correctEmotionId': correct_emotion,  # Add emotion ID for easy comparison
                'speaker_name': speaker.name,
                'scores': scores,
                'votes': {room.players[pid].name: emotion for pid, emotion in round_data.votes.items() if pid in room.players},
                'isGameComplete': is_game_complete,
                'completedRounds': completed_rounds,
                'maxRounds': room.config.max_rounds,
                'completedCycles': completed_cycles,
                'maxCycles': room.config.max_rounds
            }
            
            logger.info(f"🎉 Sending round_result event to room {room.id}")
            logger.info(f"🎉 Result data: {result_data}")
            logger.info(f"🎯 Game complete: {is_game_complete}, Phase set to: {room.phase}")
            
            await self.sio.emit('round_result', result_data, room=room.id)
            
            # Send updated room state if game continues (so frontend knows next speaker)
            if not is_game_complete:
                next_speaker = room.get_current_speaker()
                # Include player scores in the room state
                players_data = [{'name': p.name, 'score': p.score} for p in room.players.values()]
                await self.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': players_data,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': next_speaker.name if next_speaker else None
                }, room=room.id)
                logger.info(f"⏭️ Round completed, ready for next round in room {room.id}. Next speaker: {next_speaker.name if next_speaker else 'None'}")
            else:
                logger.info(f"🏆 Game completed in room {room.id}!")
                
                # Send game_complete event with final rankings
                final_rankings = sorted(
                    [{'name': player.name, 'score': player.score} for player in room.players.values()],
                    key=lambda x: x['score'],
                    reverse=True
                )
                
                # Add rank numbers
                for i, player_data in enumerate(final_rankings):
                    player_data['rank'] = i + 1
                
                logger.info(f"🏆 Sending game_complete event with rankings: {final_rankings}")
                
                await self.sio.emit('game_complete', {
                    'rankings': final_rankings,
                    'totalRounds': completed_rounds,
                    'totalCycles': completed_cycles
                }, room=room.id)
            
            logger.info(f"Round completed in room {room.id}: {correct_emotion_name}")
            
        except Exception as e:
            logger.error(f"Error completing round: {e}", exc_info=True)
    
    async def _save_round_scores(self, room, round_data, correct_votes):
        """Save individual round scores to database"""
        try:
            # Save listener scores
            for player_id, voted_emotion in round_data.votes.items():
                if voted_emotion == round_data.emotion_id:  # Correct vote
                    await self._save_score(room.id, round_data.id, player_id, 1, 'listener')
                else:  # Incorrect vote
                    await self._save_score(room.id, round_data.id, player_id, 0, 'listener')
            
            # Save speaker score
            await self._save_score(room.id, round_data.id, round_data.speaker_id, correct_votes, 'speaker')
            
            logger.info(f"Saved scores for round {round_data.id}: {len(round_data.votes)} listeners, 1 speaker")
            
        except Exception as e:
            logger.error(f"Error saving round scores: {e}", exc_info=True)
    
    async def _save_score(self, room_id, round_id, player_id, points, score_type):
        """Save a single score entry to database"""
        try:
            state_store = get_state_store()
            if hasattr(state_store, 'save_score'):
                await state_store.save_score(room_id, round_id, player_id, points, score_type)
        except Exception as e:
            logger.error(f"Error saving score for player {player_id}: {e}", exc_info=True)
    
    async def _handle_player_disconnect(self, sid):
        """Handle player disconnection"""
        try:
            session = await self.sio.get_session(sid)
            room_id = session.get('room_id')
            player_id = session.get('player_id')
            
            if room_id and player_id:
                state_store = get_state_store()
                room = await state_store.get_room(room_id)
                if room and player_id in room.players:
                    player = room.players[player_id]
                    player.is_connected = False
                    state_store = get_state_store()
                    await state_store.update_room(room)
                    
                    await self.sio.emit('player_disconnected', {
                        'playerName': player.name,
                        'playerId': player_id
                    }, room=room_id)
        except Exception as e:
            logger.error(f"Error handling disconnect: {e}")
    
    async def _check_vote_timeout(self, room_id: str, round_id: str):
        """Check if voting has timed out and force complete the round"""
        try:
            from datetime import datetime, timezone
            import asyncio
            
            # Get the timeout duration from room config
            room = await get_state_store().get_room(room_id)
            if not room:
                logger.warning(f"⏰ Timeout check: Room {room_id} not found")
                return
            timeout_seconds = room.config.vote_timeout
            logger.info(f"⏰ Starting timeout check for room {room_id}, round {round_id}, timeout: {timeout_seconds}s")
            
            # Wait for the timeout duration
            logger.info(f"⏰ Waiting {timeout_seconds} seconds for timeout...")
            await asyncio.sleep(timeout_seconds)
            logger.info(f"⏰ Timeout period elapsed for room {room_id}")
            
            # Get current room state
            state_store = get_state_store()
            room = await state_store.get_room(room_id)
            
            if not room or not room.current_round:
                logger.info(f"⏰ Vote timeout check: Round already completed in room {room_id}")
                return
                
            # Check if this is still the same round
            if room.current_round.id != round_id:
                logger.info(f"⏰ Vote timeout check: Different round active in room {room_id} (expected: {round_id}, current: {room.current_round.id})")
                return
                
            # Check if voting has already completed
            if room.current_round.is_completed:
                logger.info(f"⏰ Vote timeout check: Round already completed in room {room_id}")
                return
                
            # Check actual timeout based on voting_started_at
            if room.current_round.voting_started_at:
                # Ensure voting_started_at has timezone info
                voting_start_time = room.current_round.voting_started_at
                if voting_start_time.tzinfo is None:
                    # If offset-naive, assume it's UTC
                    voting_start_time = voting_start_time.replace(tzinfo=timezone.utc)
                
                elapsed = datetime.now(timezone.utc) - voting_start_time
                timeout_seconds = room.current_round.vote_timeout_seconds
                
                if elapsed.total_seconds() >= timeout_seconds:
                    logger.warning(f"⏰ Vote timeout in room {room_id}! Forcing round completion after {elapsed.total_seconds():.1f}s")
                    
                    # Force complete the round silently (no timeout notification)
                    await self._complete_round(room)
                else:
                    logger.info(f"⏰ Vote timeout check: Still within time limit in room {room_id}")
            else:
                logger.warning(f"⏰ Vote timeout check: No voting_started_at time in room {room_id}")
                
        except Exception as e:
            logger.error(f"Error in vote timeout check for room {room_id}: {e}", exc_info=True)