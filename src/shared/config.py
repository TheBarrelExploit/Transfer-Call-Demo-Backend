from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """settings for the application"""
    # General settings
    APP_NAME: str = "FastAPI Transfer Call"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] = ["localhost:8000", "127.0.0.1:8000", "http://127.0.0.1:8001", "http://127.0.0.1:5500"]

    # Database settings
    MONGO_URI: str 
    MONGO_DB: str 

    #Microsoft login
    MICROSOFT_CLIENT_ID: str
    MICROSOFT_CLIENT_SECRET:str
    MICROSOFT_TENANT_ID:str
    MICROSOFT_REDIRECT_URI:str

    # jwt settings
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION: int  # in minutes
 
    """Settings .env file"""
    model_config =  SettingsConfigDict(env_file=".env", case_sensitive=True)

@lru_cache     
def get_settings() -> Settings:
    """Get settings from environment variables"""
    return Settings()



