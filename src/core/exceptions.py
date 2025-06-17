from typing import Optional, Dict, Any

class BaseAppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class OpenAIError(BaseAppException):
    pass

class FrappeError(BaseAppException):
    pass

class ValidationError(BaseAppException):
    pass

class ConfigurationException(BaseAppException):
    """Exception raised for configuration errors."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, details=details) 