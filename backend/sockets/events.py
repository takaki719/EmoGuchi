import socketio
from typing import Dict, Any
from models.game import Player, GamePhase, Round
from services.state_store import state_store
import logging

logger = logging.getLogger(__name__)

class GameSocketEvents:
    def __init__(self, sio: socketio.AsyncServer):
        self.sio = sio
        self.setup_events()
    
    def setup_events(self):
        """Register all socket event handlers"""
        
        @self.sio.event
        async def connect(sid, environ):
            logger.info(f"Client connected: {sid}")
            await self.sio.emit('connected', {'message': 'Connected to EMOGUCHI server'}, room=sid)
        
        @self.sio.event
        async def disconnect(sid):
            logger.info(f"Client disconnected: {sid}")
            # Handle player disconnection
            await self._handle_player_disconnect(sid)
        
        @self.sio.event
        async def join_room(sid, data):
            """Handle player joining a room"""
            try:
                logger.info(f"join_room event received from {sid} with data: {data}")
                room_id = data.get('roomId')
                player_name = data.get('playerName')
                
                if not room_id or not player_name:
                    logger.error(f"Missing data - roomId: {room_id}, playerName: {player_name}")
                    await self.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Missing roomId or playerName'
                    }, room=sid)
                    return
                
                room = await state_store.get_room(room_id)
                if not room:
                    await self.sio.emit('error', {
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
                
                # Join socket room
                await self.sio.enter_room(sid, room_id)
                
                # Store player-room mapping
                await self.sio.save_session(sid, {
                    'player_id': player.id,
                    'room_id': room_id
                })
                
                # Notify room about player (only if it's a new player or reconnection)
                if existing_player:
                    await self.sio.emit('player_reconnected', {
                        'playerName': player.name,
                        'playerId': player.id
                    }, room=room_id)
                else:
                    await self.sio.emit('player_joined', {
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
                
                await self.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': current_speaker
                }, room=room_id)  # Send to all players in room, not just new player
                
                # If there's an active round, send round data to new player
                if room.current_round and room.phase == 'in_round':
                    await self.sio.emit('round_start', {
                        'roundId': room.current_round.id,
                        'phrase': room.current_round.phrase,
                        'speakerName': speaker.name if speaker else 'Unknown'
                    }, room=sid)
                    
                    # If the new player is the speaker, send them the emotion
                    if room.current_round.speaker_id == player.id:
                        await self.sio.emit('speaker_emotion', {
                            'roundId': room.current_round.id,
                            'emotionId': room.current_round.emotion_id
                        }, room=sid)
                
                logger.info(f"Player {player_name} joined room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in join_room: {e}", exc_info=True)
                await self.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def start_round(sid, data):
            """Start a new round (host only)"""
            try:
                session = await self.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                if not room_id or not player_id:
                    await self.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                room = await state_store.get_room(room_id)
                if not room:
                    await self.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room not found'
                    }, room=sid)
                    return
                
                player = room.players.get(player_id)
                if not player or not player.is_host:
                    await self.sio.emit('error', {
                        'code': 'EMO-403',
                        'message': 'Only host can start rounds'
                    }, room=sid)
                    return
                
                if room.phase != GamePhase.WAITING:
                    logger.warning(f"Room {room_id} is in phase {room.phase}, not WAITING. Refusing to start round.")
                    await self.sio.emit('error', {
                        'code': 'EMO-409',
                        'message': f'Room is not in waiting phase (current: {room.phase})'
                    }, room=sid)
                    return
                
                # Check minimum player count (need at least 2 players: 1 speaker + 1 listener)
                if len(room.players) < 2:
                    await self.sio.emit('error', {
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
                    await self.sio.emit('error', {
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
                
                # Send round start to all players
                await self.sio.emit('round_start', {
                    'roundId': round_data.id,
                    'phrase': phrase,
                    'speakerName': speaker.name
                }, room=room_id)
                
                # Send emotion to speaker privately
                speaker_sids = [s for s in self.sio.manager.get_participants(room_id, '/') 
                              if (await self.sio.get_session(s)).get('player_id') == speaker.id]
                
                for speaker_sid in speaker_sids:
                    await self.sio.emit('speaker_emotion', {
                        'roundId': round_data.id,
                        'emotionId': emotion_id
                    }, room=speaker_sid)
                
                logger.info(f"Round started in room {room_id}, speaker: {speaker.name}")
                
            except Exception as e:
                logger.error(f"Error in start_round: {e}", exc_info=True)
                await self.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)
        
        @self.sio.event
        async def leave_room(sid, data):
            """Handle player leaving a room"""
            try:
                session = await self.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                if not room_id or not player_id:
                    await self.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                room = await state_store.get_room(room_id)
                if not room or player_id not in room.players:
                    await self.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'Room or player not found'
                    }, room=sid)
                    return
                
                player = room.players[player_id]
                player_name = player.name
                
                # Remove player from room
                del room.players[player_id]
                await state_store.update_room(room)
                
                # Leave socket room
                await self.sio.leave_room(sid, room_id)
                
                # Clear session
                await self.sio.save_session(sid, {})
                
                # Notify remaining players
                await self.sio.emit('player_left', {
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
                
                await self.sio.emit('room_state', {
                    'roomId': room.id,
                    'players': player_names,
                    'phase': room.phase,
                    'config': room.config.dict(),
                    'currentSpeaker': current_speaker
                }, room=room_id)
                
                # Confirm to leaving player
                await self.sio.emit('left_room', {
                    'message': 'Successfully left the room'
                }, room=sid)
                
                logger.info(f"Player {player_name} left room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in leave_room: {e}", exc_info=True)
                await self.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': f'Internal server error: {str(e)}'
                }, room=sid)

        @self.sio.event
        async def submit_vote(sid, data):
            """Submit vote for current round"""
            try:
                session = await self.sio.get_session(sid)
                room_id = session.get('room_id')
                player_id = session.get('player_id')
                
                round_id = data.get('roundId')
                emotion_id = data.get('emotionId')
                
                if not room_id or not player_id:
                    await self.sio.emit('error', {
                        'code': 'EMO-401',
                        'message': 'Not authenticated'
                    }, room=sid)
                    return
                
                room = await state_store.get_room(room_id)
                if not room or not room.current_round:
                    await self.sio.emit('error', {
                        'code': 'EMO-404',
                        'message': 'No active round'
                    }, room=sid)
                    return
                
                if room.current_round.id != round_id:
                    await self.sio.emit('error', {
                        'code': 'EMO-400',
                        'message': 'Invalid round ID'
                    }, room=sid)
                    return
                
                # Don't allow speaker to vote
                if room.current_round.speaker_id == player_id:
                    await self.sio.emit('error', {
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
                    await self._complete_round(room)
                else:
                    logger.info(f"Waiting for more votes: {votes_received}/{listener_count} in room {room_id}")
                
                logger.info(f"Vote submitted by player {player_id} in room {room_id}")
                
            except Exception as e:
                logger.error(f"Error in submit_vote: {e}", exc_info=True)
                await self.sio.emit('error', {
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
            
            await self.sio.emit('round_result', {
                'roundId': round_data.id,
                'correctEmotion': correct_emotion,
                'speakerName': speaker.name,
                'scores': scores,
                'votes': {room.players[pid].name: emotion for pid, emotion in round_data.votes.items()}
            }, room=room.id)
            
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