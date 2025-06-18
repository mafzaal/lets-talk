"""Health check API endpoints."""
from fastapi import APIRouter
from datetime import datetime

from lets_talk.api.models.health import HealthResponse
from lets_talk.api.dependencies import get_scheduler_instance

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    scheduler_instance = get_scheduler_instance()
    scheduler_status = "stopped"
    
    if (scheduler_instance and 
        scheduler_instance.scheduler and 
        hasattr(scheduler_instance.scheduler, 'running')):
        scheduler_status = "running" if scheduler_instance.scheduler.running else "stopped"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        scheduler_status=scheduler_status,
        version="1.0.0"
    )
