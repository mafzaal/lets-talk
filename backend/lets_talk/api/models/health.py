"""Health check API models."""
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime


class HealthResponse(BaseModel):
    """
    Response model for basic health check.
    
    This model represents the current health status of the Let's Talk API system,
    including information about the scheduler and system status.
    """
    status: str = Field(
        description="Overall system health status",
        examples=["healthy", "unhealthy", "degraded"]
    )
    timestamp: datetime = Field(
        description="Current server timestamp when the health check was performed"
    )
    scheduler_status: str = Field(
        description="Status of the pipeline scheduler component",
        examples=["running", "stopped", "error"]
    )
    version: str = Field(
        description="Current API version",
        examples=["1.0.0"]
    )
    first_time_setup: Optional[dict] = Field(
        None,
        description="First-time setup status information",
        examples=[{
            "detection_enabled": True,
            "is_first_time": False,
            "setup_completed": True,
            "job_scheduled": False
        }]
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2025-06-18T10:30:00Z",
                "scheduler_status": "running",
                "version": "1.0.0",
                "first_time_setup": {
                    "detection_enabled": True,
                    "is_first_time": False,
                    "setup_completed": True,
                    "job_scheduled": False
                }
            }
        }
    }
