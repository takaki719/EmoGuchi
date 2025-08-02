from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import socketio
import logging
import os
import asyncio
from contextlib import asynccontextmanager
from config import settings
from api import rooms, debug
from sockets.events_minimal import GameSocketEvents
from services.database_service import DatabaseService
from services.database_state_store import DatabaseStateStore
from services.state_store import MemoryStateStore, state_store

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

# Global model initialization status
model_initialization_status = {"initialized": False, "error": None}

# Database and StateStore initialization
async def init_database():
    """Initialize database and state store"""
    global state_store
    
    # Initialize database if configured
    if settings.DATABASE_TYPE != "memory":
        logger.info(f"📊 Initializing {settings.DATABASE_TYPE} database...")
        db_service = DatabaseService()
        await db_service.initialize()
        
        # Use database-backed state store (now with current_speaker_index support)
        state_store = DatabaseStateStore(db_service)
        logger.info("✅ Database state store initialized with speaker rotation support")
    else:
        # Use in-memory state store
        state_store = MemoryStateStore()
        logger.info("💾 Using in-memory state store")
    
    # Update the state_store reference in dependent modules
    import services
    services.state_store = state_store
    rooms.state_store = state_store
    debug.state_store = state_store

async def init_ml_models():
    """Initialize ML models asynchronously"""
    global model_initialization_status
    
    try:
        logger.info("🤖 Starting ML model initialization...")
        
        # Import and initialize the emotion classifier
        from kushinada_infer import get_emotion_classifier
        classifier = get_emotion_classifier()
        
        # Trigger initialization in a separate thread to avoid blocking
        import asyncio
        import threading
        
        def init_models():
            try:
                classifier._initialize_models()
                model_initialization_status["initialized"] = True
                logger.info("✅ ML models initialized successfully")
            except Exception as e:
                model_initialization_status["error"] = str(e)
                logger.error(f"❌ ML model initialization failed: {e}")
        
        # Run initialization in background thread
        thread = threading.Thread(target=init_models)
        thread.daemon = True
        thread.start()
        
        logger.info("🚀 ML model initialization started in background")
        
    except Exception as e:
        model_initialization_status["error"] = str(e)
        logger.error(f"❌ Failed to start ML model initialization: {e}")

# Lifespan context manager for FastAPI
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    await init_database()
    # Skip ML model initialization at startup to improve boot time
    # Models will be loaded on-demand when first used
    logger.info("🚀 Application started - ML models will be loaded on-demand")
    yield
    # Shutdown (if needed)

# Create FastAPI app
app = FastAPI(
    title="EMOGUCHI API",
    description="Real-time voice emotion guessing game API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ce742f31.emoguchi.pages.dev",
        "https://emoguchi.pages.dev",
        "https://emoguchi.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
        # Additional Cloudflare Pages domains
        "https://503fc1a1.emoguchi.pages.dev",
        # Wildcard for all Cloudflare Pages preview deployments
        "https://*.emoguchi.pages.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create Socket.IO server with optional Redis adapter for scaling
def create_socketio_server():
    """Create Socket.IO server with Redis adapter if configured"""
    import socketio
    
    # Check if Redis is configured for scaling
    if settings.REDIS_URL or (settings.REDIS_HOST and settings.REDIS_PORT):
        try:
            # Try to create Redis manager for multi-instance scaling
            if settings.REDIS_URL:
                redis_url = settings.REDIS_URL
            else:
                redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{settings.REDIS_DB}"
            
            mgr = socketio.AsyncRedisManager(redis_url)
            logger.info(f"🔗 Socket.IO Redis adapter enabled: {redis_url}")
            
            return socketio.AsyncServer(
                async_mode="asgi",
                cors_allowed_origins="*",
                logger=True,
                engineio_logger=True,
                max_http_buffer_size=10 * 1024 * 1024,  # 10MB for audio data
                client_manager=mgr
            )
        except Exception as e:
            logger.warning(f"⚠️ Redis adapter failed, using single-instance mode: {e}")
    
    # Fallback to single-instance mode
    logger.info("💾 Socket.IO single-instance mode (no Redis)")
    return socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins="*",  # Allow all origins for Socket.IO
        logger=True,
        engineio_logger=True,
        max_http_buffer_size=10 * 1024 * 1024  # 10MB for audio data
    )

sio = create_socketio_server()


# Setup Socket.IO events
game_events = GameSocketEvents(sio)

# Add simple audio handling - DISABLED to use proper voice processing
# from simple_audio import setup_simple_audio_events
# setup_simple_audio_events(sio)

# Include API routers
app.include_router(rooms.router)
app.include_router(debug.router)

# ソロモード用APIの追加
from api import solo
app.include_router(solo.router)

# ルートレベルの/predict エンドポイント（フロントエンド互換性のため）
@app.post("/predict")
async def predict_emotion_root(file: UploadFile = File(...), target_emotion: int = Form(...)):
    """ルートレベルの/predict エンドポイント（/api/v1/solo/predict にリダイレクト）"""
    return await solo.predict_emotion(file, target_emotion)

# Create ASGI app that combines FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
async def root():
    return {"message": "EMOGUCHI API is running"}

@app.get("/health")
async def health_check():
    """Simple health check for Fly.io"""
    return {"status": "healthy", "message": "EMOGUCHI API is running"}

# Debug OPTIONS handler for CORS testing
@app.options("/{path:path}")
async def options_handler(path: str):
    """Handle preflight OPTIONS requests"""
    return {}

# Removed conflicting Socket.IO route that was intercepting Socket.IO connections

# 静的ファイル配信（ローカルストレージ用）
if settings.STORAGE_TYPE == "local":
    upload_dir = settings.LOCAL_AUDIO_DIR
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:socket_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )