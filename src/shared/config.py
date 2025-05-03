from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """settings for the application"""
    # General settings
    APP_NAME: str = "FastAPI Transfer Call"
    API_V1_STR: str = "/api/v1"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] = ["localhost", "127.0.0.1"]

    # Database settings
    MONGO_URI: str 
    MONGO_DB: str 
    
    # jwt settings
    JWT_SECRET: str
    JWT_ALGORITHM: str
    JWT_EXPIRATION: int  # in minutes
 
    """Settings .env file"""
    model_config =  SettingsConfigDict(env_file=".env_default",case_sensitive=True)

@lru_cache        
def get_settings() -> Settings:
    """Get settings from environment variables"""
    return Settings()



