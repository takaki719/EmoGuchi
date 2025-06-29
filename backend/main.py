from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
import logging
from config import settings
from api import rooms, debug
from sockets.events import GameSocketEvents

# Configure logging to show emoji characters
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Set specific loggers to INFO level
logging.getLogger('services.voice_processing_service').setLevel(logging.INFO)
logging.getLogger('sockets.events').setLevel(logging.INFO)
logging.getLogger('__main__').setLevel(logging.INFO)

# Initial startup log with emoji
logger = logging.getLogger(__name__)
logger.info("🎭 EMOGUCHI Backend starting up...")

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
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True,
    max_http_buffer_size=10 * 1024 * 1024  # 10MB for audio data
)

# Setup Socket.IO events
game_events = GameSocketEvents(sio)

# Add simple audio handling - DISABLED to use proper voice processing
# from simple_audio import setup_simple_audio_events
# setup_simple_audio_events(sio)

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

@app.get("/socket.io/")
async def socket_info():
    return {"message": "Socket.IO endpoint"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )