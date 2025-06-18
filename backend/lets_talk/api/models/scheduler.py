"""Scheduler-specific API models."""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from datetime import datetime
from .common import JobConfig, JobResponse


class CronJobRequest(BaseModel):
    """Request model for creating cron-based scheduled jobs."""
    job_id: str
    hour: Optional[int] = None
    minute: int = 0
    day_of_week: Optional[str] = None
    cron_expression: Optional[str] = None
    config: Optional[JobConfig] = None


class IntervalJobRequest(BaseModel):
    """Request model for creating interval-based scheduled jobs."""
    job_id: str
    minutes: Optional[int] = None
    hours: Optional[int] = None
    days: Optional[int] = None
    config: Optional[JobConfig] = None


class OneTimeJobRequest(BaseModel):
    """Request model for creating one-time scheduled jobs."""
    job_id: str
    run_date: datetime
    config: Optional[JobConfig] = None


class SchedulerStats(BaseModel):
    """Response model for scheduler statistics."""
    jobs_executed: int
    jobs_failed: int
    jobs_missed: int
    last_execution: Optional[str]
    last_error: Optional[Dict[str, Any]]
    active_jobs: int
    scheduler_running: bool


class SchedulerHealthResponse(BaseModel):
    """Response model for scheduler health check."""
    scheduler_running: bool
    total_jobs: int
    jobs_executed: int
    jobs_failed: int
    jobs_missed: int
    last_execution: Optional[str]
    healthy: bool
    warning: Optional[str] = None
