# EMOGUCHI API

This repository contains a reference implementation of the EMOGUCHI realtime voice game API using FastAPI and Socket.IO.

## Development

Install dependencies and run the server:

```bash
pip install fastapi "python-socketio[asgi]" uvicorn
uvicorn backend.main:app --reload
```

The Socket.IO server is available under `/ws` and REST endpoints are prefixed with `/api/v1`.
