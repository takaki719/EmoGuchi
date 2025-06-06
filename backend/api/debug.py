from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from services.state_store import state_store
from config import settings

router = APIRouter(prefix="/api/v1/debug", tags=["debug"])

def verify_debug_token(x_debug_token: Optional[str] = Header(None)) -> str:
    """Verify debug token"""
    if not x_debug_token or x_debug_token != settings.DEBUG_API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid debug token")
    return x_debug_token

@router.get("/rooms")
async def list_all_rooms(debug_token: str = Header(alias="X-Debug-Token")):
    """List all rooms (debug only)"""
    verify_debug_token(debug_token)
    
    rooms = await state_store.list_rooms()
    
    return {
        "rooms": [
            {
                "id": room.id,
                "phase": room.phase,
                "player_count": len(room.players),
                "connected_players": len([p for p in room.players.values() if p.is_connected]),
                "current_round": room.current_round.id if room.current_round else None,
                "votes_count": len(room.current_round.votes) if room.current_round else 0,
                "created_at": room.created_at.isoformat()
            }
            for room in rooms.values()
        ]
    }

@router.post("/rooms/{room_id}/reset")
async def reset_room_phase(room_id: str, debug_token: str = Header(alias="X-Debug-Token")):
    """Reset room to waiting phase (debug only)"""
    verify_debug_token(debug_token)
    
    room = await state_store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Reset room to waiting phase
    room.phase = "waiting"
    room.current_round = None
    await state_store.update_room(room)
    
    return {
        "message": f"Room {room_id} reset to waiting phase",
        "new_phase": room.phase
    }

@router.post("/rooms/{room_id}/complete-round")
async def force_complete_round(room_id: str, debug_token: str = Header(alias="X-Debug-Token")):
    """Force complete current round (debug only)"""
    verify_debug_token(debug_token)
    
    room = await state_store.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if not room.current_round:
        raise HTTPException(status_code=400, detail="No active round to complete")
    
    # Import here to avoid circular imports
    from sockets.events import GameSocketEvents
    from main import sio
    
    # Force complete the round
    game_events = GameSocketEvents(sio)
    await game_events._complete_round(room)
    
    return {
        "message": f"Round in room {room_id} force completed",
        "new_phase": room.phase
    }