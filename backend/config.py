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
    MAX_PLAYERS_PER_ROOM: int = int(os.getenv("MAX_PLAYERS_PER_ROOM", "16"))
    DEFAULT_VOTE_TIMEOUT: int = int(os.getenv("DEFAULT_VOTE_TIMEOUT", "30"))  # seconds
    PHRASE_CACHE_SIZE: int = int(os.getenv("PHRASE_CACHE_SIZE", "10"))
    
    # Storage settings
    STORAGE_TYPE: str = os.getenv("STORAGE_TYPE", "local")  # "local" or "s3"
    LOCAL_AUDIO_DIR: str = os.getenv("LOCAL_AUDIO_DIR", "./uploads/audio")
    
    # S3 settings (for production)
    S3_BUCKET: str = os.getenv("S3_BUCKET", "emoguchi-audio")
    S3_REGION: str = os.getenv("S3_REGION", "ap-northeast-1")
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    
    # Database settings
    DATABASE_TYPE: str = os.getenv("DATABASE_TYPE", "sqlite")  # "sqlite" or "postgresql"
    
    # SQLite settings (development)
    SQLITE_DB_PATH: str = os.getenv("SQLITE_DB_PATH", "./emoguchi.db")
    
    # PostgreSQL settings (production)
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "emoguchi")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "emoguchi")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "")
    
    @property
    def DATABASE_URL(self) -> str:
        """データベースURL生成（環境に応じて自動切り替え）"""
        if self.DATABASE_TYPE == "sqlite":
            return f"sqlite+aiosqlite:///{self.SQLITE_DB_PATH}"
        else:
            return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

settings = Settings()