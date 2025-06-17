from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PROJECT_NAME: str = "Shipra Backend"
    API_V1_STR: str = "/api/v1"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    OPENAI_API_KEY: str = "dummy_key"
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    FRAPPE_API_URL: str = "http://localhost:8000"
    FRAPPE_API_KEY: str = "dummy_key"
    FRAPPE_API_SECRET: str = "dummy_secret"
    FRAPPE_BASE_URL: str = "http://localhost:8000"
    
    TWILIO_ACCOUNT_SID: str = "dummy_sid"
    TWILIO_AUTH_TOKEN: str = "dummy_token"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 