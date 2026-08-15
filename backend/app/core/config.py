import os
from pathlib import Path
from typing import List
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "RecallBox"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "recallbox.db"
    ATTACHMENTS_DIR: Path = DATA_DIR / "attachments"
    
    # Server Configuration
    HOST: str = os.getenv("RECALLBOX_HOST", "127.0.0.1")
    PORT: int = int(os.getenv("RECALLBOX_PORT", "8765"))
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8765",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8765",
        "chrome-extension://*",
        "moz-extension://*",
    ]
    
    # AI Provider Settings
    # Options: "local" (default offline heuristic), "ollama", "openai"
    AI_PROVIDER: str = os.getenv("RECALLBOX_AI_PROVIDER", "local")
    OLLAMA_BASE_URL: str = os.getenv("RECALLBOX_OLLAMA_URL", "http://127.0.0.1:11434")
    OLLAMA_MODEL: str = os.getenv("RECALLBOX_OLLAMA_MODEL", "llama3.2")
    OLLAMA_EMBED_MODEL: str = os.getenv("RECALLBOX_OLLAMA_EMBED_MODEL", "nomic-embed-text")
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBED_MODEL: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    
    # Privacy & Telemetry
    ENABLE_TELEMETRY: bool = False
    
    def ensure_directories(self) -> None:
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

settings = Settings()
settings.ensure_directories()
