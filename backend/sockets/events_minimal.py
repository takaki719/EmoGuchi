import socketio
from typing import Dict, Any
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
                
                # Check if player with same name already exists
                existing_player = None
                for p in room.players.values():
                    if p.name == player_name:
                        existing_player = p
                        break
                
                if existing_player:
                    # Reconnect existing player
                    player = existing_player
                    player.is_connected = True
                else:
                    # Create new player
                    player = Player(name=player_name)
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
                player_names = [p.name for p in room.players.values()]
                current_speaker = None
                
                if room.current_round and room.phase == GamePhase.IN_ROUND:
                    speaker = room.get_current_speaker()
                    if speaker:
                        current_speaker = speaker.name
                
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
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
                phrase, emotion_id = await llm_service.generate_phrase_with_emotion(room.config.mode)
                
                # Get current speaker
                speaker = room.get_current_speaker()
                if not speaker:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'No players available'
                    }, room=sid)
                    return
                
                # Create round
                round_data = Round(
                    phrase=phrase,
                    emotion_id=emotion_id,
                    speaker_id=speaker.id
                )
                
                room.current_round = round_data
                room.phase = GamePhase.IN_ROUND
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Send updated room state to all players to sync phase first
                player_names = [p.name for p in room.players.values()]
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': speaker.name
                }, room=room_id)
                
                # Generate voting choices for this round
                from models.emotion import get_emotion_choices_for_voting
                choice_data = []
                if room.config.vote_type != "wheel":
                    if room.config.vote_type == "8choice":
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, emotion_id, 8)
                    else:
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, emotion_id, 4)
                    
                    choice_data = [{"id": choice.id, "name": choice.name_ja} for choice in voting_choices]
                
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
                room = await state_store.get_room(room_id)
                if not room or not room.current_round:
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
                await events_instance.sio.emit('audio_received', {
                    'audio': processed_audio,
                    'speaker_name': room.players[player_id].name,
                    'is_processed': room.config.hard_mode and processed_audio != audio_data
                }, room=room_id, skip_sid=sid)
                
                logger.info(f"Audio received and broadcast from speaker {player_id} in room {room_id}, data size: {len(audio_bytes)}")
                
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
                
                # Record vote
                room.current_round.votes[player_id] = emotion_id
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Check if all listeners have voted
                # Only count connected players (excluding speaker)
                connected_players = [p for p in room.players.values() if p.is_connected]
                listener_count = len(connected_players) - 1  # Exclude speaker
                votes_received = len(room.current_round.votes)
                
                logger.info(f"🗳️ Vote check: {votes_received}/{listener_count} votes received in room {room_id}")
                logger.info(f"🗳️ Connected players: {[p.name for p in connected_players]}")
                logger.info(f"🗳️ Speaker ID: {room.current_round.speaker_id}")
                logger.info(f"🗳️ Votes: {room.current_round.votes}")
                
                if votes_received >= listener_count and listener_count > 0:
                    logger.info(f"🎉 All votes received, completing round in room {room_id}")
                    await events_instance._complete_round(room)
                else:
                    logger.info(f"⏳ Waiting for more votes: {votes_received}/{listener_count} in room {room_id}")
                
                logger.info(f"Vote submitted by player {player_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in submit_vote: {e}", exc_info=True)
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
                if voted_emotion == correct_emotion:
                    # Listener gets point for correct guess
                    room.players[player_id].score += 1
                    correct_votes += 1
            
            # Speaker gets points based on how many guessed correctly
            speaker.score += correct_votes
            
            # Save individual scores to database
            await self._save_round_scores(room, round_data, correct_votes)
            
            # Check if game should end (reached max cycles) - BEFORE completing round
            # One cycle = all players speak once
            completed_rounds = len(room.round_history) + 1  # +1 for current round being completed
            total_players = len([p for p in room.players.values() if p.is_connected])
            completed_cycles = completed_rounds // total_players if total_players > 0 else 0
            is_game_complete = completed_cycles >= room.config.max_rounds
            
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
            room.current_speaker_index = (room.current_speaker_index + 1) % len(room.players)
            
            state_store = get_state_store()
            await state_store.update_room(room)
            
            # Send results
            scores = {player.name: player.score for player in room.players.values()}
            
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
                'votes': {room.players[pid].name: emotion for pid, emotion in round_data.votes.items()},
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
            
            if is_game_complete:
                logger.info(f"🏆 Game completed in room {room.id}!")
            else:
                logger.info(f"⏭️ Round completed, ready for next round in room {room.id}")
            
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
    
        @self.sio.event
        async def restart_game(sid, data):
            """Restart the game (host only)"""
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
                        'message': 'Only host can restart the game'
                    }, room=sid)
                    return
                
                # Reset game state
                room.phase = GamePhase.WAITING
                room.current_round = None
                room.round_history = []
                room.current_speaker_index = 0
                
                # Reset all player scores
                for player in room.players.values():
                    player.score = 0
                
                state_store = get_state_store()
                await state_store.update_room(room)
                
                # Send updated room state to all players
                player_names = [p.name for p in room.players.values()]
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.model_dump(),
                    'currentSpeaker': None
                }, room=room_id)
                
                logger.info(f"🔄 Game restarted in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in restart_game: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
    
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