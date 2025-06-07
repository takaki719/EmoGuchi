import os
from typing import List
from dotenv import load_dotenv
import pathlib

# Load .env file from project root
env_path = pathlib.Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
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
    MAX_PLAYERS_PER_ROOM: int = int(os.getenv("MAX_PLAYERS_PER_ROOM", "8"))
    DEFAULT_VOTE_TIMEOUT: int = int(os.getenv("DEFAULT_VOTE_TIMEOUT", "30"))  # seconds
    PHRASE_CACHE_SIZE: int = int(os.getenv("PHRASE_CACHE_SIZE", "10"))

settings = Settings()