import socketio
from ..main import rooms

sio = socketio.AsyncServer(async_mode="asgi")
socket_app = socketio.ASGIApp(sio, socketio_path="/ws/socket.io")

@sio.event
async def connect(sid, environ, auth):
    host_token = auth.get("hostToken") if auth else None
    # nothing to do for connect; authentication occurs on events
    pass

@sio.event
async def join_room(sid, data):
    room_id = data.get("roomId")
    player_name = data.get("playerName")
    if room_id not in rooms:
        return {"status": "error", "message": "Room not found"}
    await sio.save_session(sid, {"room_id": room_id, "playerName": player_name})
    await sio.enter_room(sid, room_id)
    state = rooms[room_id]["state"]
    state.players.append(player_name)
    await sio.emit("player_joined", {"playerName": player_name}, room=room_id)
    return {"status": "ok"}

