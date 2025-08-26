"""
Claude Guardian Main Application
FastAPI application with MCP integration, security analysis, and microservices coordination
"""

import asyncio
import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .core.config import get_settings, Settings
from .core.database import DatabaseManager
from .core.security import SecurityManager
from .api.mcp import mcp_router
from .api.security import security_router
from .api.admin import admin_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global application state
db_manager: DatabaseManager = None
security_manager: SecurityManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global db_manager, security_manager
    
    logger.info("🚀 Starting Claude Guardian v2.0.0")
    
    # Initialize configuration
    settings = get_settings()
    logger.info(f"📋 Configuration loaded: {settings.service.environment} environment")
    
    # Initialize database connections
    db_manager = DatabaseManager(settings.database)
    await db_manager.initialize()
    logger.info("🗄️ Database connections established")
    
    # Initialize security manager
    security_manager = SecurityManager(settings.security, db_manager)
    await security_manager.initialize()
    logger.info("🔒 Security manager initialized")
    
    # Seed initial data if needed
    await db_manager.seed_initial_data()
    logger.info("📊 Initial data seeding completed")
    
    # Set managers in API modules
    from .api import mcp, security, admin
    mcp.set_managers(db_manager, security_manager)
    security.set_managers(db_manager, security_manager)
    admin.set_managers(db_manager, security_manager)
    logger.info("🔌 API modules configured with managers")
    
    yield
    
    # Cleanup
    logger.info("🛑 Shutting down Claude Guardian")
    if db_manager:
        await db_manager.close()
    logger.info("✅ Shutdown completed")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Claude Guardian Security Platform",
        description="Enterprise-grade security analysis with Claude Code integration",
        version="2.0.0-alpha",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.service.debug else None,
        redoc_url="/api/redoc" if settings.service.debug else None
    )
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.local"] if settings.service.debug else ["localhost"]
    )
    
    # CORS middleware (restrictive in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"] if settings.service.debug else [],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"]
    )
    
    # Include API routers
    app.include_router(mcp_router, prefix="/api/v1/mcp", tags=["MCP"])
    app.include_router(security_router, prefix="/api/v1/security", tags=["Security"])
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Administration"])
    
    @app.get("/")
    async def root():
        """Root endpoint with system information"""
        return {
            "name": "Claude Guardian Security Platform",
            "version": "2.0.0-alpha",
            "status": "operational",
            "endpoints": {
                "mcp": "/api/v1/mcp",
                "security": "/api/v1/security", 
                "admin": "/api/v1/admin",
                "health": "/health",
                "metrics": "/metrics"
            }
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        global db_manager, security_manager
        
        health_status = {
            "status": "healthy",
            "timestamp": "2025-08-25T22:00:00Z",
            "services": {
                "database": "unknown",
                "security": "unknown",
                "mcp": "operational"
            }
        }
        
        if db_manager:
            db_health = await db_manager.health_check()
            health_status["services"]["database"] = "healthy" if db_health else "unhealthy"
        
        if security_manager:
            security_health = await security_manager.health_check()
            health_status["services"]["security"] = "healthy" if security_health else "unhealthy"
        
        # Return 503 if any critical service is unhealthy
        if health_status["services"]["database"] == "unhealthy":
            raise HTTPException(status_code=503, detail="Database unhealthy")
        
        return health_status
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        # TODO: Implement Prometheus metrics
        return {
            "metrics": "prometheus_format_metrics_here",
            "note": "Prometheus metrics implementation pending"
        }
    
    return app


# Create application instance
app = create_app()


def main():
    """Main entry point for running the application"""
    settings = get_settings()
    
    logger.info(f"🌐 Starting Claude Guardian on {settings.service.host}:{settings.service.port}")
    logger.info(f"🔧 Workers: {settings.service.workers}")
    logger.info(f"🐛 Debug mode: {settings.service.debug}")
    
    uvicorn.run(
        "claude_guardian.main:app",
        host=settings.service.host,
        port=settings.service.port,
        workers=1 if settings.service.debug else settings.service.workers,
        reload=settings.service.debug,
        log_level="debug" if settings.service.debug else "info"
    )


if __name__ == "__main__":
    main()