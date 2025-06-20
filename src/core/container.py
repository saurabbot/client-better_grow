from typing import Optional
from src.config.settings import get_settings
from src.core.logging import get_logger
from src.services.openai_service import OpenAIService
from src.services.frappe_service import FrappeService
from src.services.twillio_service import TwillioService
from src.services.session_service import SessionService
from src.repositories.frappe_repository import FrappeRepository

class Container:
    
    _instance: Optional['Container'] = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        settings = get_settings()
        self.logger = get_logger("app")
        self.openai_service = OpenAIService(settings.OPENAI_API_KEY)
        self.frappe_service = FrappeService(
            base_url=settings.FRAPPE_API_URL,
            api_key=settings.FRAPPE_API_KEY,
            api_secret=settings.FRAPPE_API_SECRET
        )
        self.twillio_service = TwillioService(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.session_service = SessionService(self.logger)
        self.settings = settings
    
    def logger(self):
        return self.logger
    
    def openai_service(self):
        return self.openai_service
    
    def frappe_service(self):
        return self.frappe_service
        
    def twillio_service(self):
        return self.twillio_service
    
    def session_service(self):
        return self.session_service 