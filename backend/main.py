from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from config import settings
from api import rooms, debug

# Create FastAPI app
app = FastAPI(
    title="EMOGUCHI API",
    description="Real-time voice emotion guessing game API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=settings.ALLOWED_ORIGINS
)

# Include API routers
app.include_router(rooms.router)
app.include_router(debug.router)

# Create ASGI app that combines FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    return {"message": "EMOGUCHI API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )