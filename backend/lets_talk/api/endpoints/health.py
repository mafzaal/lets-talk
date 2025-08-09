"""Health check API endpoints."""
from fastapi import APIRouter
from datetime import datetime, timezone

from lets_talk.api.models.health import HealthResponse
from lets_talk.api.dependencies import get_scheduler_instance

router = APIRouter(tags=["health"])


@router.get(
    "/health", 
    response_model=HealthResponse,
    summary="Health Check",
    description="""
    Performs a comprehensive health check of the Let's Talk API system.
    
    This endpoint checks:
    - Overall system status
    - Pipeline scheduler status
    - Current timestamp for debugging
    - API version information
    
    **Response Status Codes:**
    - `200`: System is healthy and operational
    - `503`: System is experiencing issues (future implementation)
    
    **Example Response:**
    ```json
    {
        "status": "healthy",
        "timestamp": "2025-06-18T10:30:00Z",
        "scheduler_status": "running",
        "version": "1.0.0"
    }
    ```
    """,
    responses={
        200: {
            "description": "System is healthy and operational",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-06-18T10:30:00Z",
                        "scheduler_status": "running",
                        "version": "1.0.0"
                    }
                }
            }
        },
        503: {
            "description": "System is experiencing issues",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-06-18T10:30:00Z",
                        "scheduler_status": "stopped",
                        "version": "1.0.0"
                    }
                }
            }
        }
    },
    tags=["health"]
)
async def health_check():
    """
    Basic health check endpoint.
    
    Returns the current status of the system including scheduler status,
    timestamp, and version information.
    """
    scheduler_instance = get_scheduler_instance()
    scheduler_status = "stopped"
    
    if (scheduler_instance and 
        scheduler_instance.scheduler and 
        hasattr(scheduler_instance.scheduler, 'running')):
        scheduler_status = "running" if scheduler_instance.scheduler.running else "stopped"
    
    # Get first-time setup status
    first_time_setup = None
    try:
        from lets_talk.core.first_time import get_first_time_status, has_first_time_marker
        from lets_talk.shared.config import FIRST_TIME_JOB_ID
        
        # Get detailed first-time status
        first_time_info = get_first_time_status()
        
        # Check if first-time job is currently scheduled
        job_scheduled = False
        if scheduler_instance and scheduler_instance.scheduler:
            job_scheduled = scheduler_instance.scheduler.get_job(FIRST_TIME_JOB_ID) is not None
        
        first_time_setup = {
            "detection_enabled": first_time_info.get("detection_enabled", False),
            "is_first_time": first_time_info.get("is_first_time", False),
            "setup_completed": has_first_time_marker(),
            "job_scheduled": job_scheduled,
            "run_pipeline_job": first_time_info.get("run_pipeline_job", False)
        }
    except Exception as e:
        # Don't fail health check if first-time info can't be retrieved
        import logging
        logger = logging.getLogger("lets_talk.api.health")
        logger.warning(f"Could not get first-time setup status: {e}")
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        scheduler_status=scheduler_status,
        version="1.0.0",
        first_time_setup=first_time_setup
    )
