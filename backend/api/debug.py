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
                "created_at": room.created_at.isoformat()
            }
            for room in rooms.values()
        ]
    }