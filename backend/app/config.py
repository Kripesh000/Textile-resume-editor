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


settings = Settings()
