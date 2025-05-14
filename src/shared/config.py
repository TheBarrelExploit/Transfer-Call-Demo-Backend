from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """settings for the application"""

    # General settings
    APP_NAME: str = "FastAPI Transfer Call"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] = [
        "localhost:8000",
        "127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:5500",
    ]

    # Database settings
    MONGO_URI: str
    MONGO_DB: str

    # Microsoft login
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET: str
    MICROSOFT_TENANT_ID: str
    MICROSOFT_REDIRECT_URI: str

    # jwt settings
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION: int  # in minutes

    # Email settings (para fastapi-mail)
    MAIL_USERNAME: str  # moralespaola888@gmail.com (del .env)
    MAIL_PASSWORD: str  # app password (del .env)
    MAIL_FROM: str  # moralespaola888@gmail.com (del .env)
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "tarificadorFastApi"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_DISPLAY_NAME: str = "tarificadorFastApi"
    MAIL_TLS: bool = False

    """ # Email settings
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "tarificadorFastApi"
    MAIL_SSL_TLS: bool = False
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True
    MAIL_DISPLAY_NAME: str = "tarificadorFastApi"
    MAIL_STARTTLS: bool = True
    MAIL_TLS: bool = False """

    """Settings .env file"""
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


@lru_cache
def get_settings() -> Settings:
    """Get settings from environment variables"""
    return Settings()
