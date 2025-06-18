# ./src/agent/webapp.py
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel
from pathlib import Path
import json
import os
import logging

# Import scheduler components
from lets_talk.scheduler import (
    PipelineScheduler, 
    create_default_scheduler_config,
    load_scheduler_config_from_file,
    save_scheduler_config_to_file
)
from lets_talk.config import OUTPUT_DIR, LOGGER_NAME

# Set up logging
logger = logging.getLogger(f"{LOGGER_NAME}.webapp")

# Global scheduler instance
scheduler_instance: Optional[PipelineScheduler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code - initialize scheduler in background mode
    global scheduler_instance
    try:
        scheduler_instance = PipelineScheduler(
            scheduler_type="background",
            max_workers=4,
            executor_type="thread",
            enable_persistence=True
        )
        scheduler_instance.start()
        logger.info("Pipeline scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        scheduler_instance = None
    
    yield
    
    # Shutdown code
    if scheduler_instance:
        try:
            scheduler_instance.shutdown()
            logger.info("Pipeline scheduler shut down successfully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

# Pydantic models for request/response
class JobConfig(BaseModel):
    data_dir: Optional[str] = None
    storage_path: Optional[str] = None
    force_recreate: bool = False
    ci_mode: bool = True
    use_chunking: bool = True
    should_save_stats: bool = True
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: Optional[str] = None
    embedding_model: Optional[str] = None
    data_dir_pattern: str = "*.md"
    blog_base_url: Optional[str] = None
    base_url: Optional[str] = None
    incremental_mode: str = "auto"
    dry_run: bool = False

class CronJobRequest(BaseModel):
    job_id: str
    hour: Optional[int] = None
    minute: int = 0
    day_of_week: Optional[str] = None
    cron_expression: Optional[str] = None
    config: Optional[JobConfig] = None

class IntervalJobRequest(BaseModel):
    job_id: str
    minutes: Optional[int] = None
    hours: Optional[int] = None
    days: Optional[int] = None
    config: Optional[JobConfig] = None

class OneTimeJobRequest(BaseModel):
    job_id: str
    run_date: datetime
    config: Optional[JobConfig] = None

class JobResponse(BaseModel):
    id: str
    name: str
    next_run_time: Optional[str]
    trigger: str

class SchedulerStats(BaseModel):
    jobs_executed: int
    jobs_failed: int
    jobs_missed: int
    last_execution: Optional[str]
    last_error: Optional[Dict[str, Any]]
    active_jobs: int
    scheduler_running: bool

def get_scheduler() -> PipelineScheduler:
    """Dependency to get the scheduler instance."""
    if scheduler_instance is None:
        raise HTTPException(status_code=503, detail="Scheduler is not available")
    return scheduler_instance

app = FastAPI(lifespan=lifespan)



# Pipeline Scheduler Management Endpoints

@app.get("/scheduler/status", response_model=SchedulerStats)
async def get_scheduler_status(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Get current scheduler status and statistics."""
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

@app.get("/scheduler/jobs", response_model=List[JobResponse])
async def list_jobs(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """List all scheduled jobs."""
    jobs = scheduler.list_jobs()
    return [JobResponse(**job) for job in jobs]

@app.post("/scheduler/jobs/cron")
async def create_cron_job(
    job_request: CronJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new cron-based scheduled job."""
    try:
        pipeline_config = job_request.config.dict() if job_request.config else {}
        
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

@app.post("/scheduler/jobs/interval")
async def create_interval_job(
    job_request: IntervalJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new interval-based scheduled job."""
    try:
        pipeline_config = job_request.config.dict() if job_request.config else {}
        
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

@app.post("/scheduler/jobs/onetime")
async def create_onetime_job(
    job_request: OneTimeJobRequest,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a new one-time scheduled job."""
    try:
        pipeline_config = job_request.config.dict() if job_request.config else {}
        
        job_id = scheduler.add_one_time_job(
            job_id=job_request.job_id,
            run_date=job_request.run_date,
            pipeline_config=pipeline_config
        )
        
        return {"message": f"One-time job '{job_id}' created successfully", "job_id": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/scheduler/jobs/{job_id}")
async def remove_job(job_id: str, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Remove a scheduled job."""
    try:
        scheduler.remove_job(job_id)
        return {"message": f"Job '{job_id}' removed successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/scheduler/jobs/{job_id}/run")
async def run_job_now(job_id: str, scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Trigger immediate execution of a scheduled job."""
    try:
        scheduler.run_job_now(job_id)
        return {"message": f"Job '{job_id}' triggered for immediate execution"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/scheduler/presets")
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

@app.post("/scheduler/presets/{preset_name}")
async def create_preset_job(
    preset_name: str,
    job_id: str,
    config: Optional[JobConfig] = None,
    scheduler: PipelineScheduler = Depends(get_scheduler)
):
    """Create a job using a preset schedule configuration."""
    presets = await get_preset_schedules()
    
    if preset_name not in presets:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_name}' not found")
    
    preset = presets[preset_name]
    pipeline_config = config.dict() if config else {}
    
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

@app.get("/scheduler/config/export")
async def export_scheduler_config(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Export current scheduler configuration."""
    try:
        config = scheduler.export_job_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scheduler/config/import")
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

@app.get("/scheduler/config/default")
async def get_default_config():
    """Get default scheduler configuration."""
    return create_default_scheduler_config()

@app.post("/scheduler/config/save")
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

@app.get("/scheduler/config/load")
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

# Pipeline Execution Endpoints

@app.post("/pipeline/run")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    config: Optional[JobConfig] = None
):
    """Run the pipeline immediately with optional configuration."""
    pipeline_config = config.model_dump() if config else {}
    pipeline_config["job_id"] = f"manual_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Use background task to avoid blocking the API
    from lets_talk.simple_pipeline_job import simple_pipeline_job
    background_tasks.add_task(simple_pipeline_job, pipeline_config)
    
    return {"message": "Pipeline execution started", "job_id": pipeline_config["job_id"]}

@app.get("/pipeline/reports")
async def list_pipeline_reports():
    """List available pipeline execution reports."""
    try:
        reports_dir = Path(OUTPUT_DIR)
        if not reports_dir.exists():
            return {"reports": []}
        
        report_files = list(reports_dir.glob("job_report_*.json"))
        reports = []
        
        for file_path in sorted(report_files, key=lambda x: x.stat().st_mtime, reverse=True):
            try:
                with open(file_path, 'r') as f:
                    report = json.load(f)
                    report["filename"] = file_path.name
                    reports.append(report)
            except Exception as e:
                logger.error(f"Failed to load report {file_path}: {e}")
        
        return {"reports": reports}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/pipeline/reports/{report_filename}")
async def get_pipeline_report(report_filename: str):
    """Get details of a specific pipeline execution report."""
    try:
        report_path = Path(OUTPUT_DIR) / report_filename
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report not found")
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Health Check Endpoints

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    scheduler_status = "stopped"
    if scheduler_instance and scheduler_instance.scheduler and hasattr(scheduler_instance.scheduler, 'running'):
        scheduler_status = "running" if scheduler_instance.scheduler.running else "stopped"
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler_status": scheduler_status,
        "version": "1.0.0"
    }

@app.get("/scheduler/health")
async def scheduler_health_check(scheduler: PipelineScheduler = Depends(get_scheduler)):
    """Detailed scheduler health check."""
    try:
        stats = scheduler.get_job_stats()
        jobs = scheduler.list_jobs()
        
        scheduler_running = False
        if scheduler.scheduler and hasattr(scheduler.scheduler, 'running'):
            scheduler_running = scheduler.scheduler.running
        
        health_status = {
            "scheduler_running": scheduler_running,
            "total_jobs": len(jobs),
            "jobs_executed": stats["jobs_executed"],
            "jobs_failed": stats["jobs_failed"],
            "jobs_missed": stats["jobs_missed"],
            "last_execution": stats["last_execution"],
            "healthy": True
        }
        
        # Consider scheduler unhealthy if too many failures
        if stats["jobs_failed"] > 0 and stats["jobs_executed"] > 0:
            failure_rate = stats["jobs_failed"] / (stats["jobs_executed"] + stats["jobs_failed"])
            if failure_rate > 0.5:  # More than 50% failure rate
                health_status["healthy"] = False
                health_status["warning"] = "High job failure rate detected"
        
        return health_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))