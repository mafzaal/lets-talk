"""Pipeline-specific API models."""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
from .common import JobConfig, BaseResponse


class PipelineRunRequest(BaseModel):
    """Request model for running pipeline."""
    config: Optional[JobConfig] = None


class PipelineRunResponse(BaseResponse):
    """Response model for pipeline execution."""
    job_id: str


class PipelineReportSummary(BaseModel):
    """Summary model for pipeline reports."""
    filename: str
    job_id: Optional[str] = None
    status: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None


class PipelineReportsResponse(BaseModel):
    """Response model for listing pipeline reports."""
    reports: List[Dict[str, Any]]
