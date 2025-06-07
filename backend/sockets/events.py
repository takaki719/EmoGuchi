import socketio
from typing import Dict, Any
from models.game import Player, GamePhase, Round
from services.state_store import state_store
import logging

logger = logging.getLogger(__name__)

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
                
                room = await state_store.get_room(room_id)
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
                
                await state_store.update_room(room)
                
                # Join socket room - 安全性チェックを追加
                try:
                    # enter_roomメソッドが存在するか確認
                    if hasattr(events_instance.sio, 'enter_room'):
                        await events_instance.sio.enter_room(sid, room_id)
                    else:
                        # 代替手段としてjoinメソッドを使用
                        await events_instance.sio.join_room(sid, room_id)
                except Exception as e:
                    logger.error(f"Error joining socket room: {e}")
                    # ルーム参加に失敗してもゲームロジックは続行
                
                # Store player-room mapping
                try:
                    await events_instance.sio.save_session(sid, {
                        'player_id': player.id,
                        'room_id': room_id
                    })
                except Exception as e:
                    logger.error(f"Error saving session: {e}")
                
                # Notify room about player (only if it's a new player or reconnection)
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
                
                # Send updated room state to ALL players in the room
                player_names = [p.name for p in room.players.values()]
                current_speaker = None
                if room.current_round and room.phase == 'in_round':
                    speaker = room.get_current_speaker()
                    if speaker:
                        current_speaker = speaker.name
                
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': current_speaker
                }, room=room_id)
                
                # If there's an active round, send round data to new player
                if room.current_round and room.phase == 'in_round':
                    # Generate voting choices for the active round
                    from models.emotion import get_emotion_choices_for_voting
                    if room.config.vote_type == "8choice":
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, room.current_round.emotion_id, 8)
                    else:
                        voting_choices = get_emotion_choices_for_voting(room.config.mode, room.current_round.emotion_id, 4)
                    
                    choice_data = [{"id": choice.id, "name": choice.name_ja} for choice in voting_choices]
                    
                    await events_instance.sio.emit('round_start', {
                        'roundId': room.current_round.id,
                        'phrase': room.current_round.phrase,
                        'speakerName': speaker.name if speaker else 'Unknown',
                        'votingChoices': choice_data
                    }, room=sid)
                    
                    # If the new player is the speaker, send them the emotion
                    if room.current_round.speaker_id == player.id:
                        # Get emotion name for display
                        from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
                        emotion_name = room.current_round.emotion_id  # fallback
                        
                        # Try to find emotion name
                        for emotion_info in BASIC_EMOTIONS.values():
                            if emotion_info.id == room.current_round.emotion_id:
                                emotion_name = emotion_info.name_ja
                                break
                        else:
                            for emotion_info in ADVANCED_EMOTIONS.values():
                                if emotion_info.id == room.current_round.emotion_id:
                                    emotion_name = emotion_info.name_ja
                                    break
                        
                        await events_instance.sio.emit('speaker_emotion', {
                            'roundId': room.current_round.id,
                            'emotionId': room.current_round.emotion_id,
                            'emotionName': emotion_name
                        }, room=sid)
                
                logger.info(f"Player {player_name} joined room {room_id}")
                
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
                await state_store.update_room(room)
                
                # Send updated room state to all players to sync phase first
                player_names = [p.name for p in room.players.values()]
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': speaker.name
                }, room=room_id)
                
                # Generate voting choices for this round
                from models.emotion import get_emotion_choices_for_voting
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
                
                # Get emotion name for display
                from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
                emotion_name = emotion_id  # fallback
                
                # Try to find emotion name
                for emotion_info in BASIC_EMOTIONS.values():
                    if emotion_info.id == emotion_id:
                        emotion_name = emotion_info.name_ja
                        break
                else:
                    for emotion_info in ADVANCED_EMOTIONS.values():
                        if emotion_info.id == emotion_id:
                            emotion_name = emotion_info.name_ja
                            break
                
                # Send emotion to speaker privately - find all speaker sessions
                speaker_sids = []
                try:
                    if hasattr(events_instance.sio, 'manager') and hasattr(events_instance.sio.manager, 'get_participants'):
                        for sid_check in events_instance.sio.manager.get_participants(room_id, '/'):
                            try:
                                session = await events_instance.sio.get_session(sid_check)
                                if session.get('player_id') == speaker.id:
                                    speaker_sids.append(sid_check)
                            except:
                                continue
                except Exception as e:
                    logger.warning(f"Could not get participants for room {room_id}: {e}")
                
                # Send directly to each speaker session to ensure delivery
                for speaker_sid in speaker_sids:
                    await events_instance.sio.emit('speaker_emotion', {
                        'roundId': round_data.id,
                        'emotionId': emotion_id,
                        'emotionName': emotion_name,
                        'speakerId': speaker.id
                    }, room=speaker_sid)
                
                # Also send to entire room as backup with speaker filter in frontend
                await events_instance.sio.emit('speaker_emotion', {
                    'roundId': round_data.id,
                    'emotionId': emotion_id,
                    'emotionName': emotion_name,
                    'speakerId': speaker.id
                }, room=room_id)
                
                logger.info(f"Round started in room {room_id}, speaker: {speaker.name}")
                
            except Exception as e:
                logger.error(f"Error in start_round: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def leave_room(sid, data):
            """Handle player leaving a room"""
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
                
                room = await state_store.get_room(room_id)
                if not room or player_id not in room.players:
                    await events_instance.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room or player not found'
                    }, room=sid)
                    return
                
                player = room.players[player_id]
                player_name = player.name
                
                # Remove player from room
                del room.players[player_id]
                await state_store.update_room(room)
                
                # Leave socket room - 安全性チェックを追加
                try:
                    if hasattr(events_instance.sio, 'leave_room'):
                        await events_instance.sio.leave_room(sid, room_id)
                    else:
                        logger.warning("leave_room method not available on sio instance")
                except Exception as e:
                    logger.error(f"Error leaving socket room: {e}")
                
                # Clear session
                try:
                    await events_instance.sio.save_session(sid, {})
                except Exception as e:
                    logger.error(f"Error clearing session: {e}")
                
                # Notify remaining players
                await events_instance.sio.emit('player_left', {
                    'playerName': player_name,
                    'playerId': player_id
                }, room=room_id)
                
                # Send updated room state to remaining players
                player_names = [p.name for p in room.players.values()]
                current_speaker = None
                if room.current_round and room.phase == 'in_round':
                    speaker = room.get_current_speaker()
                    if speaker:
                        current_speaker = speaker.name
                
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': current_speaker
                }, room=room_id)
                
                # Confirm to leaving player
                await events_instance.sio.emit('left_room', {
                    'message': 'Successfully left the room'
                }, room=sid)
                
                logger.info(f"Player {player_name} left room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in leave_room: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)

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
                
                await state_store.update_room(room)
                
                # Send updated room state to all players
                player_names = [p.name for p in room.players.values()]
                await events_instance.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': None
                }, room=room_id)
                
                logger.info(f"Game restarted in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in restart_game: {e}", exc_info=True)
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
                await state_store.update_room(room)
                
                # Check if all listeners have voted
                # Only count connected players (excluding speaker)
                connected_players = [p for p in room.players.values() if p.is_connected]
                listener_count = len(connected_players) - 1  # Exclude speaker
                votes_received = len(room.current_round.votes)
                
                logger.info(f"Vote check: {votes_received}/{listener_count} votes received in room {room_id}")
                
                if votes_received >= listener_count and listener_count > 0:
                    logger.info(f"All votes received, completing round in room {room_id}")
                    await events_instance._complete_round(room)
                else:
                    logger.info(f"Waiting for more votes: {votes_received}/{listener_count} in room {room_id}")
                
                logger.info(f"Vote submitted by player {player_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in submit_vote: {e}", exc_info=True)
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
    
    async def _handle_player_disconnect(self, sid: str):
        """Handle player disconnection"""
        try:
            session = await self.sio.get_session(sid)
            room_id = session.get('room_id')
            player_id = session.get('player_id')
            
            if room_id and player_id:
                room = await state_store.get_room(room_id)
                if room and player_id in room.players:
                    player = room.players[player_id]
                    player.is_connected = False
                    await state_store.update_room(room)
                    
                    await self.sio.emit('player_disconnected', {
                        'playerName': player.name,
                        'playerId': player_id
                    }, room=room_id)
                    
        except Exception as e:
            logger.error(f"Error handling disconnect: {e}")
    
    async def _complete_round(self, room):
        """Complete current round and calculate scores"""
        try:
            if not room.current_round:
                return
            
            round_data = room.current_round
            correct_emotion = round_data.emotion_id
            
            # Calculate scores
            speaker = room.players[round_data.speaker_id]
            correct_votes = 0
            
            for player_id, voted_emotion in round_data.votes.items():
                if voted_emotion == correct_emotion:
                    # Listener gets point for correct guess
                    room.players[player_id].score += 1
                    correct_votes += 1
            
            # Speaker gets points based on how many guessed correctly
            speaker.score += correct_votes
            
            # Mark round as completed
            round_data.is_completed = True
            room.round_history.append(round_data)
            room.current_round = None
            room.phase = GamePhase.RESULT
            
            # Move to next speaker
            room.current_speaker_index = (room.current_speaker_index + 1) % len(room.players)
            
            await state_store.update_room(room)
            
            # Send results
            scores = {player.name: player.score for player in room.players.values()}
            
            # Get emotion name for display
            from models.emotion import BASIC_EMOTIONS, ADVANCED_EMOTIONS
            correct_emotion_name = correct_emotion  # fallback
            
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
            
            # Check if game should end (reached max rounds)
            completed_rounds = len(room.round_history)
            is_game_complete = completed_rounds >= room.config.max_rounds
            
            await self.sio.emit('round_result', {
                'roundId': round_data.id,
                'correctEmotion': correct_emotion_name,
                'correctEmotionId': correct_emotion,  # Add emotion ID for easy comparison
                'speakerName': speaker.name,
                'scores': scores,
                'votes': {room.players[pid].name: emotion for pid, emotion in round_data.votes.items()},
                'isGameComplete': is_game_complete,
                'completedRounds': completed_rounds,
                'maxRounds': room.config.max_rounds
            }, room=room.id)
            
            # If game is complete, send final rankings
            if is_game_complete:
                # Create final rankings sorted by score
                final_rankings = sorted(
                    [{'name': player.name, 'score': player.score} for player in room.players.values()],
                    key=lambda x: x['score'],
                    reverse=True
                )
                
                # Add rank numbers
                for i, player_data in enumerate(final_rankings):
                    player_data['rank'] = i + 1
                
                await self.sio.emit('game_complete', {
                    'rankings': final_rankings,
                    'totalRounds': completed_rounds
                }, room=room.id)
                
                # Transition to a completed state briefly, then waiting
                room.phase = GamePhase.CLOSED
            else:
                # Transition back to waiting phase after result
                room.phase = GamePhase.WAITING
            
            await state_store.update_room(room)
            
            # Send updated room state to all players to ensure UI is synchronized
            player_names = [p.name for p in room.players.values()]
            await self.sio.emit('room_state', {
                'roomId': room.id,
                'players': player_names,
                'phase': room.phase,
                'config': room.config.dict(),
                'currentSpeaker': None
            }, room=room.id)
            
            logger.info(f"Round completed in room {room.id}")
            
        except Exception as e:
            logger.error(f"Error completing round: {e}")