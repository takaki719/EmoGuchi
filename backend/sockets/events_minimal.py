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
                logger.error(f"Error in join_room: {e}")
                await events_instance.sio.emit('error', {
                    'code': 'EMO-500',
                    'message': 'Internal server error'
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