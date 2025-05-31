import os
from typing import List, Optional
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import computed_field

class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Gil-WhatsApp-Bot"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]
    
    # MongoDB settings
    MONGODB_HOST: str = "mongo"
    MONGODB_PORT: int = 27017
    MONGODB_DB_NAME: str = "gil_whatsapp_bot"
    MONGO_USER: Optional[str] = None
    MONGO_PASSWORD: Optional[str] = None
    
    @computed_field
    @property
    def MONGODB_URL(self) -> str:
        """Construct MongoDB URL with or without authentication."""
        if self.MONGO_USER and self.MONGO_PASSWORD:
            return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB_NAME}?authSource=admin"
        else:
            return f"mongodb://{self.MONGODB_HOST}:{self.MONGODB_PORT}/{self.MONGODB_DB_NAME}"
    
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