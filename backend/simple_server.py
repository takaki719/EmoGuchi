#!/usr/bin/env python3

import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(title="Simple Socket.IO Test")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins="*",
    logger=True
)

@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")
    await sio.emit('connected', {'message': 'Connected to test server'}, room=sid)

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    print(f"join_room event from {sid}: {data}")
    try:
        room_id = data.get('roomId', 'test-room')
        player_name = data.get('playerName', 'TestPlayer')
        
        await sio.enter_room(sid, room_id)
        await sio.emit('room_state', {
            'roomId': room_id,
            'players': [player_name],
            'phase': 'waiting'
        }, room=sid)
        
        print(f"Player {player_name} joined room {room_id}")
        
    except Exception as e:
        print(f"Error in join_room: {e}")
        await sio.emit('error', {
            'code': 'EMO-500',
            'message': str(e)
        }, room=sid)

# Create ASGI app
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    return {"message": "Simple Socket.IO test server"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    print("Starting simple Socket.IO test server on port 8000...")
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)