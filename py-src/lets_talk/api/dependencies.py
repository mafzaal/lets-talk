"""Shared API dependencies and utilities."""
from typing import Optional
from fastapi import HTTPException, Depends
from lets_talk.core.scheduler.manager import PipelineScheduler

# Global scheduler instance
scheduler_instance: Optional[PipelineScheduler] = None

def get_scheduler() -> PipelineScheduler:
    """Dependency to get the scheduler instance."""
    if scheduler_instance is None:
        raise HTTPException(status_code=503, detail="Scheduler is not available")
    return scheduler_instance

def set_scheduler_instance(scheduler: PipelineScheduler) -> None:
    """Set the global scheduler instance."""
    global scheduler_instance
    scheduler_instance = scheduler

def get_scheduler_instance() -> Optional[PipelineScheduler]:
    """Get the current scheduler instance."""
    return scheduler_instance
