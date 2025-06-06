from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from models.game import (
    Room, RoomConfig, CreateRoomRequest, CreateRoomResponse, 
    RoomState, ErrorResponse, GamePhase
)
from services.state_store import state_store
import uuid
import logging

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

def validate_room_id(room_id: str) -> bool:
    """Validate custom room ID format"""
    import re
    # Allow alphanumeric characters, Japanese characters (hiragana, katakana, kanji), and some symbols
    # Length between 3-20 characters
    # ひらがな: \u3041-\u3096
    # カタカナ: \u30a1-\u30fc  
    # 漢字: \u4e00-\u9faf
    # 長音符号: \u30fc
    pattern = r'^[a-zA-Z0-9\u3041-\u3096\u30a1-\u30fc\u4e00-\u9faf]{3,20}$'
    return bool(re.match(pattern, room_id))

@router.post("/rooms", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """Create a new room"""
    try:
        logger = logging.getLogger(__name__)
        
        room_config = RoomConfig(
            mode=request.mode,
            vote_type=request.vote_type,
            speaker_order=request.speaker_order
        )
        
        # Handle custom room ID
        if request.room_id and request.room_id.strip():
            # Validate format
            if not validate_room_id(request.room_id.strip()):
                raise HTTPException(
                    status_code=400, 
                    detail="合言葉は3-20文字で、英数字・ひらがな・カタカナ・漢字のみ使用できます"
                )
            
            # Use trimmed room ID
            trimmed_room_id = request.room_id.strip()
            
            # Check if room ID already exists
            existing_room = await state_store.get_room(trimmed_room_id)
            if existing_room:
                # Return existing room info instead of error
                logger.info(f"Room {trimmed_room_id} already exists, returning existing room info")
                return CreateRoomResponse(
                    roomId=existing_room.id,
                    hostToken=existing_room.host_token
                )
            
            # Create room with custom ID
            room = Room(id=trimmed_room_id, config=room_config)
        else:
            # Create room with auto-generated ID
            room = Room(config=room_config)
            # Debug: Test if auto-generated ID would pass validation
            logger.info(f"Auto-generated room ID: {room.id}, validates: {validate_room_id(room.id)}")
        
        await state_store.create_room(room)
        
        # Debug logging
        logger.info(f"Created room with ID: {room.id}")
        
        return CreateRoomResponse(
            roomId=room.id,
            hostToken=room.host_token
        )
    except HTTPException:
        raise
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
    phrase_data = await llm_service.generate_batch_phrases(batch_size, room.config.mode)
    phrases = [phrase for phrase, _ in phrase_data]
    
    return {"phrases": phrases}