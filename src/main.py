from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from src.api.v1.endpoints import webhook, health
from src.core.logging import setup_logging, logger
from src.config.settings import get_settings

# Load settings
settings = get_settings()

# Configure logging
setup_logging()

# Custom logger test for Railway logs
logger.info("🚀 Custom logger test: App startup log should appear in Railway logs")

# Create FastAPI app
app = FastAPI(
    title="Shipra Backend",
    description="Backend service for Shipra WhatsApp integration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    webhook.router,
    prefix="/api/v1",
    tags=["webhook"]
)

app.include_router(
    health.router,
    tags=["health"]
)

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    ) 