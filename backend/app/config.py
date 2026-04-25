import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./textile.db"
    secret_key: str = "change-me-to-a-random-secret-key"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    # Regex pattern for additional allowed origins (e.g. Vercel preview deployments)
    cors_allow_origin_regex: str = r"https://.*\.vercel\.app"
    tectonic_path: str = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "tectonic")
    access_token_expire_hours: int = 24

    model_config = {"env_file": ".env", "extra": "ignore"}
    
    @property
    def async_database_url(self) -> str:
        """Return async-compatible database URL"""
        url = self.database_url
        
        # If it's SQLite, it's already async-compatible
        if "sqlite" in url:
            return url
            
        # Convert PostgreSQL URL to use asyncpg
        if url and url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            
        return url


settings = Settings()