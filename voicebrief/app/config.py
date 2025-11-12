"""
Configuration management for VoiceBrief application.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


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

    # Google Docs (Service Account - optional)
    google_credentials_file: Optional[str] = None
    google_credentials_json: Optional[str] = None

    # Google OAuth2 (for user authentication)
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    google_oauth_redirect_uri: Optional[str] = None

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
