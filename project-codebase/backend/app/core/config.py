from pydantic_settings import BaseSettings
from typing import List, Optional, Union, Literal

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Project Nexus"
    API_V1_STR: str = "/api/v1"
    
    # Database
    MONGO_CONNECTION_STRING: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "project_nexus"
    
    # Security
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Google API Config
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GMAIL_POLL_LABEL: str = "Project-Nexus-Intake"
    DRIVE_WATCH_FOLDER_ID: Optional[str] = None
    
    # CORS - Allow all origins for development/production
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # AI / LLM
    GROQ_API_KEY: str
    GOOGLE_API_KEY: Optional[str] = None # For Gemini Embeddings
    
    # Supported Groq Models for Fallback
    GROQ_MODEL_1: str = "llama-3.3-70b-versatile"
    GROQ_MODEL_2: str = "llama-3.1-70b-versatile"
    GROQ_MODEL_3: str = "mixtral-8x7b-32768"
    GROQ_MODEL_4: str = "llama-4-scout-17b-16e-instruct"
    
    LLM_MODEL: str = "gemini-1.5-flash"
    
    @property
    def GROQ_MODELS(self) -> List[str]:
        # User requested 5 models total: Primary + 4 Fallbacks
        # We handle potential duplicates by using a set if needed, but here we list explicitly
        return [
            self.LLM_MODEL, 
            self.GROQ_MODEL_1, 
            self.GROQ_MODEL_2, 
            self.GROQ_MODEL_3, 
            self.GROQ_MODEL_4
        ]
    EMBEDDING_PROVIDER: Literal["huggingface", "gemini", "ollama"] = "gemini"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2" # HF or Ollama model name
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GNEWS_API_KEY: Optional[str] = None
    
    # In-Memory Settings
    WATCHDOG_POLL_INTERVAL: int = 300  # 5 minutes
    
    # Basecamp API
    BASECAMP_ACCESS_TOKEN: Optional[str] = None
    BASECAMP_ACCOUNT_ID: Optional[str] = None
    BASECAMP_PROJECT_IDS: Optional[str] = None  # Comma-separated
    BASECAMP_USER_AGENT: str = "Basecamp Export (contact@example.com)"
    BASECAMP_SYNC_INTERVAL: int = 86400  # 24 hours

    # Vector Database
    VECTOR_STORE_PROVIDER: Literal["chroma", "pinecone"] = "chroma"
    PINECONE_API_KEY: Optional[str] = None
    PINECONE_INDEX_NAME: str = "project-nexus"

    # Data Source Controls
    ENABLE_BASECAMP: bool = True
    ENABLE_GMAIL: bool = True
    ENABLE_DRIVE: bool = True
    ENABLE_LOCAL_FILES: bool = True
    ENABLE_LOCAL_FILES: bool = True
    ENABLE_STARTUP_AUTOMATION: bool = True
    
    # Email / SMTP
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: str = "Project Nexus"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()
