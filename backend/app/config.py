from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./textile.db"
    secret_key: str = "change-me-to-a-random-secret-key"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    cors_origins: str = "http://localhost:3000"
    tectonic_path: str = "tectonic"
    access_token_expire_hours: int = 24

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
