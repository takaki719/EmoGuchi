from fastapi import FastAPI, Header, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Literal, Optional
import uuid

from .sockets.room import socket_app
from .store import store

app = FastAPI(title="EMOGUCHI API", version="v1")

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://emoguchi.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount Socket.IO app
app.mount("/ws", socket_app)

# In-memory state store
DEBUG_TOKEN = "debug"

class RoomConfig(BaseModel):
    mode: Literal["basic", "advanced"] = "basic"
    voteType: Literal[4, 8] = 4
    speakerOrder: Literal["random", "ordered"] = "random"

class RoomCreated(BaseModel):
    roomId: str
    hostToken: str

class RoomState(BaseModel):
    roomId: str
    players: List[str] = []
    phase: Literal["waiting", "in_round", "result"] = "waiting"
    config: RoomConfig

class PrefetchRequest(BaseModel):
    batchSize: int

class PrefetchResult(BaseModel):
    phrases: List[str]


# Dependency to check host token
async def require_host_token(room_id: str, authorization: Optional[str] = Header(None)):
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing host token")
    token = authorization.split(" ", 1)[1]
    room = store.rooms.get(room_id)
    if not room or room["hostToken"] != token:
        raise HTTPException(status_code=403, detail="Invalid host token")
    return room


@app.post("/api/v1/rooms", response_model=RoomCreated, status_code=201)
async def create_room(config: RoomConfig):
    room_id = str(uuid.uuid4())
    host_token = str(uuid.uuid4())
    room_state = RoomState(roomId=room_id, config=config)
    store.rooms[room_id] = {"state": room_state, "hostToken": host_token}
    return RoomCreated(roomId=room_id, hostToken=host_token)


@app.get("/api/v1/rooms/{room_id}", response_model=RoomState)
async def get_room(room_id: str):
    room = store.rooms.get(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return room["state"]


@app.delete("/api/v1/rooms/{room_id}")
async def delete_room(room_id: str, room=Depends(require_host_token)):
    store.rooms.pop(room_id, None)
    return {"ok": True}


@app.post("/api/v1/rooms/{room_id}/prefetch", response_model=PrefetchResult)
async def prefetch(room_id: str, req: PrefetchRequest, room=Depends(require_host_token)):
    phrases = [f"phrase {i}" for i in range(req.batchSize)]
    return PrefetchResult(phrases=phrases)


@app.get("/api/v1/debug/rooms")
async def debug_rooms(x_debug_token: Optional[str] = Header(None)):
    if x_debug_token != DEBUG_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid debug token")
    return {"rooms": list(store.rooms.keys())}

