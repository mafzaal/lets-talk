"""Health check API models."""
from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class HealthResponse(BaseModel):
    """Response model for basic health check."""
    status: str
    timestamp: datetime
    scheduler_status: str
    version: str
