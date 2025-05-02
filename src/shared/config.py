from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """settings for the application"""
    # General settings
    APP_NAME: str = "FastAPI Transfer Call"
    PORT: int = 8000
    DEBUG: bool = True
    ALLOWED_HOSTS: list[str] 

    # Database settings
    MONGO_URI: str 
    MONGO_DB: str 
    
    # jwt settings
    JWT_SECRET: str
    JWT_ALGORITHM: str
    
    """Settings .env file"""
    model_config =  SettingsConfigDict(env_file=".env",case_sensitive=True)

@lru_cache        
def get_settings() -> Settings:
    """Get settings from environment variables"""
    return Settings()



