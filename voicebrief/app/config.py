"""
Configuration management for VoiceBrief application.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"

    # ElevenLabs
    elevenlabs_api_key: str
    elevenlabs_voice_id: str = "EXAVITQu4vr4xnSDxMaL"  # Rachel

    # Supabase
    supabase_url: str
    supabase_key: str
    supabase_bucket: str = "voicebrief-audio"

    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_default_channel: str = "#daily-briefings"

    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_base_url: str = "http://localhost:8000"
    environment: str = "development"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
