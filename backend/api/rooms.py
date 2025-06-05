from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from models.game import (
    Room, RoomConfig, CreateRoomRequest, CreateRoomResponse, 
    RoomState, ErrorResponse, GamePhase
)
from services.state_store import state_store
import uuid

router = APIRouter(prefix="/api/v1", tags=["rooms"])

async def verify_host_token(room_id: str, authorization: Optional[str]) -> str:
    """Verify host token for room operations"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    token = authorization.split(" ")[1]
    room = await state_store.get_room(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if room.host_token != token:
        raise HTTPException(status_code=403, detail="Invalid host token")
    
    return token

@router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """Create a new room"""
    try:
        room_config = RoomConfig(
            mode=request.mode,
            vote_type=request.vote_type,
            speaker_order=request.speaker_order
        )
        
        room = Room(config=room_config)
        await state_store.create_room(room)
        
        return CreateRoomResponse(
            roomId=room.id,
            hostToken=room.host_token
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")

@router.get("/rooms/{room_id}", response_model=RoomState)
async def get_room(room_id: str):
    """Get room state"""
    room = await state_store.get_room(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    player_names = [player.name for player in room.players.values()]
    current_speaker = None
    
    if room.current_round and room.phase == GamePhase.IN_ROUND:
        speaker = room.get_current_speaker()
        if speaker:
            current_speaker = speaker.name
    
    return RoomState(
        roomId=room.id,
        players=player_names,
        phase=room.phase,
        config=room.config,
        currentSpeaker=current_speaker
    )

@router.delete("/rooms/{room_id}")
async def delete_room(room_id: str, authorization: Optional[str] = Header(None)):
    """Delete a room (host only)"""
    await verify_host_token(room_id, authorization)
    await state_store.delete_room(room_id)
    return {"ok": True}

@router.post("/rooms/{room_id}/prefetch")
async def prefetch_phrases(
    room_id: str,
    batch_size: int = 5,
    authorization: Optional[str] = Header(None)
):
    """Prefetch phrases for next rounds (host only)"""
    await verify_host_token(room_id, authorization)
    room = await state_store.get_room(room_id)
    
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    from services.llm_service import llm_service
    
    # Generate phrases with LLM
    phrase_data = await llm_service.generate_batch_phrases(batch_size, room.config.mode.value)
    phrases = [phrase for phrase, _ in phrase_data]
    
    return {"phrases": phrases}