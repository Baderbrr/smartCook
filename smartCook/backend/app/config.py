from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables or a .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./smartcook.db"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    seed_on_startup: bool = True
    # How many days before its expiry date an ingredient counts as "expiring soon".
    expiring_within_days: int = 3


settings = Settings()
