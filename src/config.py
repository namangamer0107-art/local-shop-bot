import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    META_API_TOKEN: str = os.getenv("META_API_TOKEN", "")
    WHATSAPP_PHONE_NUMBER_ID: str = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
    VERIFY_TOKEN: str = os.getenv("VERIFY_TOKEN", "jain_shubh_masale_secret_123")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    DEFAULT_TENANT: str = os.getenv("DEFAULT_TENANT", "jain_shubh_masale")
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
