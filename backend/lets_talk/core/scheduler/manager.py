"""Pipeline scheduler manager."""
import os
import logging
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor as APSThreadPoolExecutor
from apscheduler.executors.pool import ProcessPoolExecutor as APSProcessPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from lets_talk.shared.config import (
    OUTPUT_DIR, LOGGER_NAME, DATABASE_URL,
    DEFAULT_JOB_ENABLED, DEFAULT_JOB_ID, DEFAULT_JOB_CRON_HOUR, 
    DEFAULT_JOB_CRON_MINUTE, DEFAULT_JOB_INCREMENTAL_MODE, 
    DEFAULT_JOB_CI_MODE, DEFAULT_JOB_DRY_RUN
)

logger = logging.getLogger(f"{LOGGER_NAME}.scheduler")


class PipelineScheduler:
    """Advanced scheduler for the blog data pipeline using APScheduler."""
    
    def __init__(self, 
                 scheduler_type: str = "background",
                 job_store_url: Optional[str] = None,
                 max_workers: int = 4,
                 executor_type: str = "thread",
                 enable_persistence: bool = True):
        """Initialize the pipeline scheduler."""
        self.scheduler_type = scheduler_type
        self.max_workers = max_workers
        self.executor_type = executor_type
        self.enable_persistence = enable_persistence
        
        # Set up job store
        if enable_persistence and job_store_url:
            self.job_store_url = job_store_url
        elif enable_persistence:
            # Use configured database URL
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            self.job_store_url = DATABASE_URL
        else:
            self.job_store_url = None
        
        self.scheduler: Optional[Union[BlockingScheduler, BackgroundScheduler]] = None
        self.job_stats = {
            "jobs_executed": 0,
            "jobs_failed": 0,
            "jobs_missed": 0,
            "last_execution": None,
            "last_error": None
        }
        
        self._setup_scheduler()
        
    def _setup_scheduler(self):
        """Set up the APScheduler instance with job stores and executors."""
        # Configure job stores
        if self.job_store_url:
            jobstore = SQLAlchemyJobStore(url=self.job_store_url)
        else:
            jobstore = MemoryJobStore()
        
        # Configure executors
        if self.executor_type == "thread":
            executor = APSThreadPoolExecutor(max_workers=self.max_workers)
        else:
            executor = APSProcessPoolExecutor(max_workers=self.max_workers)
        
        job_defaults = {
            'coalesce': False,
            'max_instances': 3,
            'misfire_grace_time': 3600  # 1 hour
        }
        
        # Create scheduler
        if self.scheduler_type == "blocking":
            self.scheduler = BlockingScheduler(
                jobstores={'default': jobstore},
                executors={'default': executor},
                job_defaults=job_defaults
            )
        else:
            self.scheduler = BackgroundScheduler(
                jobstores={'default': jobstore},
                executors={'default': executor},
                job_defaults=job_defaults
            )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
        
        logger.info(f"Scheduler setup completed: type={self.scheduler_type}, "
                   f"executor={self.executor_type}, workers={self.max_workers}")
    
    def _job_executed(self, event):
        """Handle job execution events."""
        self.job_stats["jobs_executed"] += 1
        self.job_stats["last_execution"] = datetime.now(timezone.utc).isoformat()
        logger.info(f"Job executed successfully: {event.job_id}")
    
    def _job_error(self, event):
        """Handle job error events."""
        self.job_stats["jobs_failed"] += 1
        self.job_stats["last_error"] = {
            "job_id": event.job_id,
            "exception": str(event.exception),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        logger.error(f"Job failed: {event.job_id}, error: {event.exception}")
    
    def _job_missed(self, event):
        """Handle job missed events."""
        self.job_stats["jobs_missed"] += 1
        logger.warning(f"Job missed: {event.job_id}")
    
    def start(self):
        """Start the scheduler."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            self.scheduler.start()
            logger.info("Scheduler started successfully")
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    def shutdown(self, wait: bool = True):
        """Shutdown the scheduler."""
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=wait)
                logger.info("Scheduler shut down successfully")
            except Exception as e:
                logger.error(f"Error shutting down scheduler: {e}")
                raise
    
    def add_cron_job(self, 
                     job_id: str,
                     cron_expression: Optional[str] = None,
                     hour: Optional[int] = None,
                     minute: int = 0,
                     day_of_week: Optional[str] = None,
                     pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """Add a cron-based scheduled job."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        # Import here to avoid circular imports
        from lets_talk.core.pipeline.jobs import simple_pipeline_job
        
        if cron_expression:
            trigger = CronTrigger.from_crontab(cron_expression)
        else:
            trigger = CronTrigger(hour=hour, minute=minute, day_of_week=day_of_week)
        

        if pipeline_config is None:
            pipeline_config = {}


        if "job_id" not in pipeline_config or pipeline_config["job_id"] is None:
            pipeline_config["job_id"] = job_id


        self.scheduler.add_job(
            func=simple_pipeline_job,
            trigger=trigger,
            args=[pipeline_config or {}],
            id=job_id,
            name=f"Cron Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added cron job: {job_id}")
        return job_id
    
    def add_interval_job(self,
                        job_id: str,
                        minutes: Optional[int] = None,
                        hours: Optional[int] = None,
                        days: Optional[int] = None,
                        pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """Add an interval-based scheduled job."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        # Import here to avoid circular imports
        from lets_talk.core.pipeline.jobs import simple_pipeline_job
        
        trigger = IntervalTrigger(days=days, hours=hours, minutes=minutes)

        if pipeline_config is None:
            pipeline_config = {}


        if "job_id" not in pipeline_config or pipeline_config["job_id"] is None:
            pipeline_config["job_id"] = job_id

        
        self.scheduler.add_job(
            func=simple_pipeline_job,
            trigger=trigger,
            args=[pipeline_config or {}],
            id=job_id,
            name=f"Interval Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added interval job: {job_id}")
        return job_id
    
    def add_one_time_job(self,
                        job_id: str,
                        run_date: datetime,
                        pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """Add a one-time scheduled job."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        # Import here to avoid circular imports
        from lets_talk.core.pipeline.jobs import simple_pipeline_job
        
        trigger = DateTrigger(run_date=run_date)
        
        self.scheduler.add_job(
            func=simple_pipeline_job,
            trigger=trigger,
            args=[pipeline_config or {}],
            id=job_id,
            name=f"One-time Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added one-time job: {job_id}")
        return job_id
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
            raise
    
    def run_job_now(self, job_id: str):
        """Trigger immediate execution of a scheduled job."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now(timezone.utc))
                logger.info(f"Triggered immediate execution of job: {job_id}")
            else:
                raise ValueError(f"Job {job_id} not found")
        except Exception as e:
            logger.error(f"Failed to trigger job {job_id}: {e}")
            raise
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "config": job.args[0],
                
            })
        
        return jobs
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        return self.job_stats.copy()
    
    def export_job_config(self) -> Dict[str, Any]:
        """Export current job configuration."""
        if not self.scheduler:
            return {"jobs": []}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            job_config = {
                "id": job.id,
                "name": job.name,
                "trigger": {
                    "type": type(job.trigger).__name__,
                    "fields": job.trigger.fields if hasattr(job.trigger, 'fields') else {}
                },
                "args": job.args,
                "kwargs": job.kwargs
            }
            jobs.append(job_config)
        
        return {"jobs": jobs}
    
    def import_job_config(self, config: Dict[str, Any]) -> int:
        """Import job configuration."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        imported_count = 0
        jobs = config.get("jobs", [])
        
        for job_config in jobs:
            try:
                # This is a simplified import - in practice you'd need to
                # reconstruct the proper trigger and function references
                logger.info(f"Would import job: {job_config['id']}")
                imported_count += 1
            except Exception as e:
                logger.error(f"Failed to import job {job_config.get('id', 'unknown')}: {e}")
        
        return imported_count

    def has_default_job(self) -> bool:
        """Check if the default pipeline job already exists."""
        if not self.scheduler:
            return False
        
        try:
            job = self.scheduler.get_job(DEFAULT_JOB_ID)
            return job is not None
        except Exception as e:
            logger.error(f"Error checking for default job: {e}")
            return False

    def create_default_job(self) -> str:
        """Create the default pipeline job with default configuration."""
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")
        
        if self.has_default_job():
            logger.info(f"Default job '{DEFAULT_JOB_ID}' already exists, skipping creation")
            return DEFAULT_JOB_ID
        
        # Import JobConfig here to avoid circular imports
        try:
            from lets_talk.api.models.common import JobConfig
            
            # Create default job configuration
            default_config = JobConfig.with_defaults()
            
            # Override specific defaults for the default job
            pipeline_config = {
                "job_id": DEFAULT_JOB_ID,
                "incremental_mode": DEFAULT_JOB_INCREMENTAL_MODE,
                "ci_mode": DEFAULT_JOB_CI_MODE,
                "dry_run": DEFAULT_JOB_DRY_RUN,
                "force_recreate": False,  # Use incremental by default
                "should_save_stats": True,
                # Include all other defaults from JobConfig
                **default_config.model_dump()
            }
            
            # Create the cron job
            job_id = self.add_cron_job(
                job_id=DEFAULT_JOB_ID,
                hour=DEFAULT_JOB_CRON_HOUR,
                minute=DEFAULT_JOB_CRON_MINUTE,
                pipeline_config=pipeline_config
            )
            
            logger.info(f"Created default pipeline job '{job_id}' scheduled for {DEFAULT_JOB_CRON_HOUR:02d}:{DEFAULT_JOB_CRON_MINUTE:02d}")
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create default job: {e}")
            raise

    def initialize_default_job_if_needed(self) -> bool:
        """Initialize the default job if it's enabled and doesn't exist."""
        if not DEFAULT_JOB_ENABLED:
            logger.debug("Default job scheduling is disabled")
            return False
        
        if not self.scheduler:
            logger.warning("Scheduler not initialized, cannot create default job")
            return False
        
        try:
            if self.has_default_job():
                logger.info(f"Default job '{DEFAULT_JOB_ID}' already exists")
                return True
            
            logger.info("Creating default pipeline job...")
            self.create_default_job()
            logger.info("Default pipeline job created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize default job: {e}")
            return False
