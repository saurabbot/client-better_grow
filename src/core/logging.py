import logging
import sys
import structlog
from typing import Any, Dict

def setup_logging() -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)

class LoggerAdapter:
    """Adapter for structured logging with context."""
    
    def __init__(self, logger: structlog.BoundLogger):
        self.logger = logger
        self.context: Dict[str, Any] = {}
    
    def bind(self, **kwargs: Any) -> 'LoggerAdapter':
        """Bind context to the logger."""
        self.context.update(kwargs)
        return self
    
    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        """Log with context."""
        self.logger.bind(**self.context).log(level, event, **kwargs)
    
    def info(self, event: str, **kwargs: Any) -> None:
        self._log("info", event, **kwargs)
    
    def error(self, event: str, **kwargs: Any) -> None:
        self._log("error", event, **kwargs)
    
    def warning(self, event: str, **kwargs: Any) -> None:
        self._log("warning", event, **kwargs)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        self._log("debug", event, **kwargs) 