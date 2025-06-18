"""Main FastAPI application setup and configuration."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging

from lets_talk.api.dependencies import set_scheduler_instance
from lets_talk.api.endpoints import scheduler, pipeline, health
from lets_talk.core.scheduler.manager import PipelineScheduler
from lets_talk.shared.config import LOGGER_NAME

# Set up logging
logger = logging.getLogger(f"{LOGGER_NAME}.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown tasks."""
    # Startup code - initialize scheduler in background mode
    try:
        scheduler_instance = PipelineScheduler(
            scheduler_type="background",
            max_workers=4,
            executor_type="thread",
            enable_persistence=True
        )
        scheduler_instance.start()
        set_scheduler_instance(scheduler_instance)
        logger.info("Pipeline scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        set_scheduler_instance(None)
    
    yield
    
    # Shutdown code
    scheduler_instance = None
    try:
        from lets_talk.api.dependencies import get_scheduler_instance
        scheduler_instance = get_scheduler_instance()
        if scheduler_instance:
            scheduler_instance.shutdown()
            logger.info("Pipeline scheduler shut down successfully")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Let's Talk API",
        description="AI-driven chat system for websites with pipeline management",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Include routers
    app.include_router(scheduler.router)
    app.include_router(pipeline.router)
    app.include_router(health.router)
    
    return app


# Create the app instance
app = create_app()
