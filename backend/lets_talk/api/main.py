"""Main FastAPI application setup and configuration."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from lets_talk.shared.config import ALLOW_ORIGINS_URLS
import logging

from lets_talk.api.dependencies import set_scheduler_instance
from lets_talk.api.endpoints import scheduler, pipeline, health, settings
from lets_talk.core.startup import (
    startup_fastapi_application, 
    shutdown_application,
    log_startup_summary
)
from lets_talk.shared.config import LOGGER_NAME

# Set up logging
logger = logging.getLogger(f"{LOGGER_NAME}.api")

# Global variable to store startup info for shutdown
_startup_info = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks."""
    global _startup_info
    
    # Startup sequence
    try:
        logger.info("Starting FastAPI application...")
        
        # Use consolidated startup system
        _startup_info = startup_fastapi_application(
            app_name="FastAPI API Server",
            scheduler_config={
                "scheduler_type": "background",
                "max_workers": 20,
                "enable_persistence": None  # Auto-decide based on DB health
            },
            fail_on_migration_error=False,  # Don't fail completely if migration fails
            fail_on_scheduler_error=False,  # Don't fail completely if scheduler fails  
            fail_on_default_job_error=False  # Don't fail completely if default job fails
        )
        
        # Log startup summary
        log_startup_summary(_startup_info)
        
        # Set scheduler instance for dependency injection
        if _startup_info.get("scheduler_instance"):
            set_scheduler_instance(_startup_info["scheduler_instance"])
            logger.info("Scheduler instance set for FastAPI dependencies")
        else:
            logger.warning("No scheduler instance available for FastAPI dependencies")
        
        # Log final startup status
        if _startup_info["success"]:
            logger.info("🚀 FastAPI application startup completed successfully")
        else:
            logger.warning("⚠️ FastAPI application started with some issues")
            for error in _startup_info.get("errors", []):
                logger.error(f"   • {error}")
        
    except Exception as e:
        logger.error(f"Failed to start FastAPI application: {e}")
        logger.exception("Startup error details:")
        # Continue with minimal functionality
        logger.warning("Continuing with minimal functionality...")
        _startup_info = {
            "success": False,
            "errors": [str(e)],
            "scheduler_instance": None
        }
    
    yield
    
    # Shutdown sequence
    try:
        logger.info("Shutting down FastAPI application...")
        if _startup_info:
            shutdown_status = shutdown_application(_startup_info, timeout=30)
            if shutdown_status["success"]:
                logger.info("✅ FastAPI application shutdown completed successfully")
            else:
                logger.warning("⚠️ FastAPI application shutdown completed with issues")
                for error in shutdown_status.get("errors", []):
                    logger.error(f"   • {error}")
        else:
            logger.info("No startup info available, skipping component shutdown")
    except Exception as e:
        logger.error(f"Error during FastAPI application shutdown: {e}")
        logger.exception("Shutdown error details:")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Let's Talk API",
        description="""
        ## Let's Talk API
        
        AI-driven chat system for websites with comprehensive pipeline management capabilities.
        
        ### Features
        
        * **Pipeline Management**: Create, schedule, and monitor AI processing pipelines
        * **Real-time Health Monitoring**: Check system status and component health
        * **Scheduler Control**: Start, stop, and manage background task scheduling
        * **AI Chat Integration**: Process and respond to user queries intelligently
        
        ### Getting Started
        
        1. Check the health endpoint to ensure the system is running
        2. Explore the pipeline endpoints to create and manage processing workflows
        3. Use the scheduler endpoints to control background task execution
        
        ### Authentication
        
        Currently, this API does not require authentication. This may change in future versions.
        
        ### Rate Limiting
        
        Rate limiting is not currently implemented but may be added in future versions.
        """,
        version="0.1.1",
        terms_of_service="https://thedataguy.pro/lets-talk/",
        contact={
            "name": "Let's Talk Support",
            "url": "https://thedataguy.pro/lets-talk/",
            "email": "support@thedataguy.pro",
        },
        license_info={
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
        openapi_tags=[
            {
                "name": "health",
                "description": "Health check and system status endpoints. Use these to monitor the overall health of the system and its components."
            },
            {
                "name": "pipeline",
                "description": "Pipeline management endpoints. Create, execute, and monitor AI processing pipelines for content analysis and generation."
            },
            {
                "name": "scheduler",
                "description": "Background task scheduler endpoints. Control the execution of scheduled tasks and monitor their status."
            },
            {
                "name": "settings",
                "description": "System settings management endpoints. View, update, and restore system configurations through a user-friendly API."
            },
        ],
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    

    # Enable CORS for development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOW_ORIGINS_URLS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # Include routers
    app.include_router(scheduler.router)
    app.include_router(pipeline.router)
    app.include_router(health.router)
    app.include_router(settings.router)

    
    def custom_openapi():
        """Custom OpenAPI schema generation with enhanced documentation."""
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        
        # Add custom schema information
        openapi_schema["info"]["x-logo"] = {
            "url": "https://example.com/logo.png"
        }
        
        # Add server information
        # openapi_schema["servers"] = [
        #     {
        #         "url": "/",
        #         "description": "Development server"
        #     },
        #     {
        #         "url": "https://api.example.com",
        #         "description": "Production server"
        #     }
        # ]
        
        # Add security schemes (for future use)
        openapi_schema["components"]["securitySchemes"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    return app


# Create the app instance
app = create_app()
