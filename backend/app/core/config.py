import os
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Gil-WhatsApp-Bot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # MongoDB settings
    MONGODB_URL: Optional[str] = "mongodb://dummy:27017/test"
    MONGODB_DB_NAME: Optional[str] = "gil_whatsapp_bot"
    MONGO_USER: Optional[str] = "gil_whatsapp_bot"
    MONGO_PASSWORD: Optional[str] = "gil_whatsapp_bot"
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-4"
    RETRIEVAL_LLM_MODEL: Optional[str] = "gpt-3.5-turbo"
    GENERATION_LLM_MODEL: str = "gpt-4"
    
    # WhatsApp API settings
    WHATSAPP_API_URL: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 