import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Algebra Integral DEX Screener Adapter",
    description="HTTP adapter for integrating Algebra Integral with DEX Screener",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(router, prefix="")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "name": "Algebra Integral DEX Screener Adapter",
        "version": "1.0.0",
        "networks": settings.active_networks,
        "status": "healthy"
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    from app.services import subgraph_service
    
    network_status = {}
    for network in settings.active_networks:
        try:
            latest_block = await subgraph_service.get_latest_block(network)
            network_status[network] = {
                "connected": latest_block is not None,
                "latest_block": latest_block.get("blockNumber") if latest_block else None,
                "subgraph_available": True
            }
        except Exception as e:
            network_status[network] = {
                "connected": False,
                "error": str(e),
                "subgraph_available": False
            }
    
    return {
        "status": "healthy",
        "networks": network_status
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )
