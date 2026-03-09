"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    database_url: str = "sqlite+aiosqlite:///./slice_groups.db"
    max_group_size: int = 5

    model_config = {"env_prefix": "SLICE_"}


settings = Settings()
