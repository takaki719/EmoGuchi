# EMOGUCHI API

This repository contains a reference implementation of the EMOGUCHI realtime voice game API using FastAPI and Socket.IO.

## Development

Install dependencies and run the server:

```bash
pip install fastapi "python-socketio[asgi]" uvicorn
uvicorn backend.main:app --reload
```

The Socket.IO server is available under `/ws` and REST endpoints are prefixed with `/api/v1`.

## Example Socket.IO client

Below is a minimal example using the JavaScript client:

```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8000/ws');

// join a room
socket.emit('join_room', { roomId: '<room-id>', playerName: 'Alice' });

// receive round start broadcast
socket.on('round_start', ({ roundId, phrase }) => {
  console.log(`Round ${roundId}:`, phrase);
  // submit a vote (example emotionId: 1)
  socket.emit('submit_vote', { roundId, emotionId: 1 });
});

// receive final scores
socket.on('round_result', (payload) => {
  console.log('Result:', payload);
});
```
