"""Scheduler management API endpoints."""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import os

from lets_talk.api.dependencies import get_scheduler
from lets_talk.api.models.scheduler import (
    CronJobRequest, IntervalJobRequest, OneTimeJobRequest,
    SchedulerStats, SchedulerHealthResponse
)
from lets_talk.api.models.common import JobResponse
from lets_talk.core.scheduler.manager import PipelineScheduler
from lets_talk.core.scheduler.config import (
    create_default_scheduler_config,
    load_scheduler_config_from_file,
    save_scheduler_config_to_file
)
from lets_talk.shared.config import OUTPUT_DIR

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get(
    "/status", 
    response_model=SchedulerStats,
    summary="Get Scheduler Status",
    description="""
    Retrieve comprehensive statistics and status information about the pipeline scheduler.
    
    This endpoint provides:
    - Job execution statistics (successful, failed, missed)
    - Last execution and error information
    - Current number of active scheduled jobs
    - Scheduler running state
    
    **Use Cases:**
    - Monitor scheduler health in dashboards
    - Debug scheduling issues
    - Performance monitoring and alerting
    
    **Response includes:**
    - `jobs_executed`: Total number of successfully executed jobs
    - `jobs_failed`: Total number of failed job executions
    - `jobs_missed`: Total number of missed job executions
    - `last_execution`: Timestamp of the most recent job execution
    - `last_error`: Details of the most recent error (if any)
    - `active_jobs`: Current number of scheduled jobs
    - `scheduler_running`: Whether the scheduler is currently active
    """,
    responses={
        200: {
            "description": "Scheduler status retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "jobs_executed": 150,
                        "jobs_failed": 2,
                        "jobs_missed": 0,
                        "last_execution": "2025-06-18T10:25:00Z",
                        "last_error": None,
                        "active_jobs": 5,
                        "scheduler_running": True
                    }
                }
            }
        },
        503: {
            "description": "Scheduler is not available or not properly initialized"
        }
    }
)
async def get_scheduler_status(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """
    Get current scheduler status and statistics.
    
    Returns comprehensive information about the scheduler's current state,
    including execution statistics and active job counts.
    """
    stats = scheduler.get_job_stats()
    jobs = scheduler.list_jobs()
    
    scheduler_running = False
    if scheduler.scheduler and hasattr(scheduler.scheduler, 'running'):
        scheduler_running = scheduler.scheduler.running
    
    return SchedulerStats(
        jobs_executed=stats["jobs_executed"],
        jobs_failed=stats["jobs_failed"],
        jobs_missed=stats["jobs_missed"],
        last_execution=stats["last_execution"],
        last_error=stats["last_error"],
        active_jobs=len(jobs),
        scheduler_running=scheduler_running
    )


@router.get(
    "/jobs", 
    response_model=List[JobResponse],
    summary="List All Scheduled Jobs",
    description="""
    Retrieve a comprehensive list of all currently scheduled jobs in the system.
    
    This endpoint returns detailed information about each scheduled job including:
    - Job ID and name
    - Job type (cron, interval, one-time)
    - Schedule configuration
    - Next execution time
    - Job status and metadata
    - args and kwargs used for job execution
    
    **Use Cases:**
    - View all active schedules
    - Monitor job configurations
    - Debug scheduling conflicts
    - Audit scheduled tasks
    
    **Job Types:**
    - **Cron Jobs**: Execute on cron-like schedules (e.g., daily, weekly)
    - **Interval Jobs**: Execute at regular intervals (e.g., every 30 minutes)
    - **One-time Jobs**: Execute once at a specific time
    """,
    responses={
        200: {
            "description": "List of scheduled jobs retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "blog_update_daily",
                            "name": "Daily Blog Update",
                            "type": "cron",
                            "next_run": "2025-06-19T09:00:00Z",
                            "status": "scheduled",
                            "args": {},
                            "kwargs": {}
                        },
                        {
                            "id": "health_check_interval",
                            "name": "Health Check",
                            "type": "interval",
                            "next_run": "2025-06-18T10:35:00Z",
                            "status": "scheduled",
                            "args": {},
                            "kwargs": {}
                        }
                    ]
                }
            }
        },
        503: {
            "description": "Scheduler is not available"
        }
    }
)
async def list_jobs(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """
    List all scheduled jobs.
    
    Returns a comprehensive list of all jobs currently scheduled in the system,
    including their configuration and status information.
    """
    jobs = scheduler.list_jobs()
    return [JobResponse(**job) for job in jobs]


@router.post("/jobs/cron")
async def create_cron_job(
    job_request: CronJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new cron-based scheduled job."""
    try:
        pipeline_config = job_request.config.model_dump() if job_request.config else {}
        
        job_id = scheduler.add_cron_job(
            job_id=job_request.job_id,
            cron_expression=job_request.cron_expression,
            hour=job_request.hour,
            minute=job_request.minute,
            day_of_week=job_request.day_of_week,
            pipeline_config=pipeline_config
        )
        
        return {"message": f"Cron job '{job_id}' created successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/interval")
async def create_interval_job(
    job_request: IntervalJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new interval-based scheduled job."""
    try:
        pipeline_config = job_request.config.model_dump() if job_request.config else {}
        
        job_id = scheduler.add_interval_job(
            job_id=job_request.job_id,
            minutes=job_request.minutes,
            hours=job_request.hours,
            days=job_request.days,
            pipeline_config=pipeline_config
        )
        
        return {"message": f"Interval job '{job_id}' created successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/jobs/onetime")
async def create_onetime_job(
    job_request: OneTimeJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new one-time scheduled job."""
    try:
        pipeline_config = job_request.config.model_dump() if job_request.config else {}
        
        job_id = scheduler.add_one_time_job(
            job_id=job_request.job_id,
            run_date=job_request.run_date,
            pipeline_config=pipeline_config
        )
        
        return {"message": f"One-time job '{job_id}' created successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Get details of a specific scheduled job."""
    try:
        jobs = scheduler.list_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
        return JobResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/jobs/{job_id}")
async def update_job(job_id: str, job_data: dict, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Update a scheduled job."""
    try:
        # Remove the old job first
        scheduler.remove_job(job_id)
        
        # Create new job with updated configuration
        job_type = job_data.get('jobType', 'cron')
        config = job_data.get('config', {})
        
        if job_type == 'cron':
            scheduler.add_cron_job(
                job_id=job_id,
                hour=job_data.get('hour'),
                minute=job_data.get('minute'),
                day_of_week=job_data.get('day_of_week'),
                cron_expression=job_data.get('cron_expression'),
                config=config
            )
        elif job_type == 'interval':
            scheduler.add_interval_job(
                job_id=job_id,
                minutes=job_data.get('minutes'),
                hours=job_data.get('hours'),
                days=job_data.get('days'),
                config=config
            )
        elif job_type == 'onetime':
            scheduler.add_one_time_job(
                job_id=job_id,
                run_date=job_data.get('run_date'),
                config=config
            )
        
        # Return the updated job
        jobs = scheduler.list_jobs()
        job = next((j for j in jobs if j['id'] == job_id), None)
        if not job:
            raise HTTPException(status_code=404, detail=f"Failed to update job '{job_id}'")
        return JobResponse(**job)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/jobs/{job_id}")
async def remove_job(job_id: str, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Remove a scheduled job."""
    try:
        scheduler.remove_job(job_id)
        return {"message": f"Job '{job_id}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/run")
async def run_job_now(job_id: str, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Trigger immediate execution of a scheduled job."""
    try:
        scheduler.run_job_now(job_id)
        return {"message": f"Job '{job_id}' triggered for immediate execution"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presets")
async def get_preset_schedules():
    """Get common preset schedule configurations."""
    presets = {
        "daily_2am": {
            "description": "Daily at 2:00 AM",
            "type": "cron",
            "hour": 2,
            "minute": 0
        },
        "weekly_sunday_1am": {
            "description": "Weekly on Sunday at 1:00 AM",
            "type": "cron",
            "day_of_week": "sun",
            "hour": 1,
            "minute": 0
        },
        "hourly": {
            "description": "Every hour",
            "type": "interval",
            "hours": 1
        },
        "every_30_minutes": {
            "description": "Every 30 minutes",
            "type": "interval",
            "minutes": 30
        },
        "twice_daily": {
            "description": "Twice daily (6 AM and 6 PM)",
            "type": "multiple",
            "schedules": [
                {"hour": 6, "minute": 0},
                {"hour": 18, "minute": 0}
            ]
        }
    }
    return presets


@router.post("/presets/{preset_name}")
async def create_preset_job(
    preset_name: str,
    job_id: str,
    config: Optional[Dict[str, Any]] = None,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a job using a preset schedule configuration."""
    presets = await get_preset_schedules()
    
    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    preset = presets[preset_name]
    pipeline_config = config or {}
    
    try:
        if preset["type"] == "cron":
            job_id = scheduler.add_cron_job(
                job_id=job_id,
                hour=preset.get("hour"),
                minute=preset.get("minute", 0),
                day_of_week=preset.get("day_of_week"),
                pipeline_config=pipeline_config
            )
        elif preset["type"] == "interval":
            job_id = scheduler.add_interval_job(
                job_id=job_id,
                minutes=preset.get("minutes"),
                hours=preset.get("hours"),
                days=preset.get("days"),
                pipeline_config=pipeline_config
            )
        elif preset["type"] == "multiple":
            # Create multiple jobs for schedules like twice daily
            job_ids = []
            for i, schedule in enumerate(preset["schedules"]):
                sub_job_id = f"{job_id}_{i+1}"
                sub_job_id = scheduler.add_cron_job(
                    job_id=sub_job_id,
                    hour=schedule.get("hour"),
                    minute=schedule.get("minute", 0),
                    day_of_week=schedule.get("day_of_week"),
                    pipeline_config=pipeline_config
                )
                job_ids.append(sub_job_id)
            return {"message": f"Multiple jobs created with preset '{preset_name}'", "job_ids": job_ids}
        
        return {"message": f"Job '{job_id}' created with preset '{preset_name}'", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/export")
async def export_scheduler_config(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Export current scheduler configuration."""
    try:
        config = scheduler.export_job_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config/import")
async def import_scheduler_config(
    config: Dict[str, Any],
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Import scheduler configuration."""
    try:
        imported_count = scheduler.import_job_config(config)
        return {"message": f"Successfully imported {imported_count} jobs"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/config/default")
async def get_default_config():
    """Get default scheduler configuration."""
    return create_default_scheduler_config()


@router.post("/config/save")
async def save_config_to_file(
    config: Dict[str, Any],
    filename: Optional[str] = None
):
    """Save scheduler configuration to file."""
    try:
        if filename is None:
            filename = os.path.join(OUTPUT_DIR, "scheduler_config.json")
        
        save_scheduler_config_to_file(config, filename)
        return {"message": f"Configuration saved to {filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config/load")
async def load_config_from_file(
    filename: Optional[str] = None,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Load scheduler configuration from file."""
    try:
        if filename is None:
            filename = os.path.join(OUTPUT_DIR, "scheduler_config.json")
        
        if not os.path.exists(filename):
            raise HTTPException(status_code=404, detail=f"Configuration file {filename} not found")
        
        config = load_scheduler_config_from_file(filename)
        imported_count = scheduler.import_job_config(config)
        return {"message": f"Loaded configuration from {filename}, imported {imported_count} jobs"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/health", response_model=SchedulerHealthResponse)
async def scheduler_health_check(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Detailed scheduler health check."""
    try:
        stats = scheduler.get_job_stats()
        jobs = scheduler.list_jobs()
        
        scheduler_running = False
        if scheduler.scheduler and hasattr(scheduler.scheduler, 'running'):
            scheduler_running = scheduler.scheduler.running
        
        health_status = SchedulerHealthResponse(
            scheduler_running=scheduler_running,
            total_jobs=len(jobs),
            jobs_executed=stats["jobs_executed"],
            jobs_failed=stats["jobs_failed"],
            jobs_missed=stats["jobs_missed"],
            last_execution=stats["last_execution"],
            healthy=True
        )
        
        # Consider scheduler unhealthy if too many failures
        if stats["jobs_failed"] > 0 and stats["jobs_executed"] > 0:
            failure_rate = stats["jobs_failed"] / (stats["jobs_executed"] + stats["jobs_failed"])
            if failure_rate > 0.5:  # More than 50% failure rate
                health_status.healthy = False
                health_status.warning = "High job failure rate detected"
        
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
