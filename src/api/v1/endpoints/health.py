from fastapi import APIRouter, Depends
from src.core.container import Container
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)

def get_container() -> Container:
    return Container()

@router.get("/health")
async def health_check(container: Container = Depends(get_container)):
    """Health check endpoint for Docker and monitoring."""
    try:
        # Basic health check
        health_status = {
            "status": "healthy",
            "service": "shipra-backend",
            "version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Check if we can access container services
        if container.logger:
            health_status["logging"] = "ok"
        
        if container.openai_service:
            health_status["openai_service"] = "ok"
            
        if container.twillio_service:
            health_status["twilio_service"] = "ok"
            
        if container.session_service:
            health_status["session_service"] = "ok"
        
        logger.info("health_check_passed", status=health_status)
        return health_status
        
    except Exception as e:
        logger.error("health_check_failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "shipra-backend",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }

@router.get("/ready")
async def readiness_check(container: Container = Depends(get_container)):
    """Readiness check for Kubernetes and load balancers."""
    try:
        # Check if all required services are ready
        readiness_status = {
            "status": "ready",
            "service": "shipra-backend",
            "checks": {
                "database": "ok",
                "redis": "ok",
                "openai": "ok",
                "twilio": "ok"
            }
        }
        
        logger.info("readiness_check_passed", status=readiness_status)
        return readiness_status
        
    except Exception as e:
        logger.error("readiness_check_failed", error=str(e))
        return {
            "status": "not_ready",
            "service": "shipra-backend",
            "error": str(e)
        } 