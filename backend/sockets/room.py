import socketio
from ..store import store

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
    if room_id not in store.rooms:
        return {"status": "error", "message": "Room not found"}
    await sio.save_session(sid, {"room_id": room_id, "playerName": player_name})
    await sio.enter_room(sid, room_id)
    state = store.rooms[room_id]["state"]
    state.players.append(player_name)
    await sio.emit("player_joined", {"playerName": player_name}, room=room_id)
    return {"status": "ok"}


@sio.event
async def round_start(sid, data):
    """Host starts a new round and broadcast to all players."""
    session = await sio.get_session(sid)
    room_id = session.get("room_id") if session else None
    if not room_id or room_id not in rooms:
        return {"status": "error", "message": "Room not found"}

    round_id = data.get("roundId")
    phrase = data.get("phrase")
    room = rooms[room_id]
    room["current_round"] = {"roundId": round_id, "phrase": phrase, "votes": {}}
    room["state"].phase = "in_round"
    await sio.emit("round_start", {"roundId": round_id, "phrase": phrase}, room=room_id)
    return {"status": "ok"}


@sio.event
async def submit_vote(sid, data):
    """Receive a vote from a listener."""
    session = await sio.get_session(sid)
    room_id = session.get("room_id") if session else None
    player_name = session.get("playerName") if session else None
    if not room_id or room_id not in rooms:
        return {"status": "error", "message": "Room not found"}

    room = rooms[room_id]
    current = room.get("current_round")
    if not current or current.get("roundId") != data.get("roundId"):
        return {"status": "error", "message": "Invalid round"}

    emotion_id = data.get("emotionId")
    current["votes"][player_name] = emotion_id
    return {"status": "ok"}


@sio.event
async def round_result(sid, data):
    """Broadcast final result of the round to all players."""
    session = await sio.get_session(sid)
    room_id = session.get("room_id") if session else None
    if not room_id or room_id not in rooms:
        return {"status": "error", "message": "Room not found"}

    room = rooms[room_id]
    room["state"].phase = "result"

    current = room.get("current_round", {})
    round_id = current.get("roundId")
    votes = current.get("votes", {})
    scores = [{"playerName": p, "vote": v} for p, v in votes.items()]
    payload = {
        "roundId": round_id,
        "correctEmotion": data.get("correctEmotion"),
        "scores": scores,
    }
    await sio.emit("round_result", payload, room=room_id)
    return {"status": "ok"}

