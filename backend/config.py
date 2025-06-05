import os
from typing import List

class Settings:
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8002
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://emoguchi.vercel.app"
    ]
    
    # API settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    DEBUG_API_TOKEN: str = os.getenv("DEBUG_API_TOKEN", "debug-token-123")
    
    # Game settings
    MAX_PLAYERS_PER_ROOM: int = 8
    DEFAULT_VOTE_TIMEOUT: int = 30  # seconds
    PHRASE_CACHE_SIZE: int = 10

settings = Settings()