"""
Pipeline Scheduler Module

This module provides scheduled execution capabilities for the blog data pipeline
using APScheduler with executor pools for reliable task execution.

Features:
- Cron-style scheduling
- Interval-based scheduling  
- One-time scheduling
- Persistent job storage
- Thread/process pool executors
- Error handling and retries
- Job monitoring and logging
"""

import os
import sys
import logging
import signal
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List, Union
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

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

# Import pipeline functionality
# Note: Avoid importing from pipeline module here to prevent circular imports
from lets_talk.config import (
    LOG_LEVEL, LOGGER_NAME, OUTPUT_DIR, DATA_DIR, VECTOR_STORAGE_PATH,
    FORCE_RECREATE, USE_CHUNKING, SHOULD_SAVE_STATS, CHUNK_SIZE, CHUNK_OVERLAP,
    QDRANT_COLLECTION, EMBEDDING_MODEL, DEFAULT_METADATA_CSV_FILENAME
)

# Set up logging
logger = logging.getLogger(f"{LOGGER_NAME}.scheduler")

class PipelineScheduler:
    """
    Advanced scheduler for the blog data pipeline using APScheduler.
    
    Supports multiple scheduling patterns with executor pools and persistent storage.
    """
    
    def __init__(self, 
                 scheduler_type: str = "background",
                 job_store_url: Optional[str] = None,
                 max_workers: int = 4,
                 executor_type: str = "thread",
                 enable_persistence: bool = True):
        """
        Initialize the pipeline scheduler.
        
        Args:
            scheduler_type: "blocking" or "background"
            job_store_url: SQLite URL for persistent job storage (None for memory)
            max_workers: Maximum number of concurrent workers
            executor_type: "thread" or "process"
            enable_persistence: Whether to enable persistent job storage
        """
        self.scheduler_type = scheduler_type
        self.max_workers = max_workers
        self.executor_type = executor_type
        self.enable_persistence = enable_persistence
        
        # Set up job store
        if enable_persistence and job_store_url:
            self.job_store_url = job_store_url
        elif enable_persistence:
            # Default SQLite job store in output directory
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            self.job_store_url = f"sqlite:///{OUTPUT_DIR}/scheduler_jobs.db"
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
        # Temporarily disable signal handlers for testing
        # self._setup_signal_handlers()
        
    def _setup_scheduler(self):
        """Set up the APScheduler instance with job stores and executors."""
        
        # Configure job stores
        jobstores = {}
        if self.job_store_url:
            jobstores['default'] = SQLAlchemyJobStore(url=self.job_store_url)
            logger.info(f"Using persistent job store: {self.job_store_url}")
        else:
            jobstores['default'] = MemoryJobStore()
            logger.info("Using in-memory job store")
        
        # Configure executors
        executors = {}
        if self.executor_type == "thread":
            executors['default'] = APSThreadPoolExecutor(max_workers=self.max_workers)
            logger.info(f"Using ThreadPoolExecutor with {self.max_workers} workers")
        else:
            executors['default'] = APSProcessPoolExecutor(max_workers=self.max_workers)
            logger.info(f"Using ProcessPoolExecutor with {self.max_workers} workers")
        
        # Job defaults
        job_defaults = {
            'coalesce': True,  # Combine multiple pending executions into one
            'max_instances': 1,  # Maximum number of concurrent instances
            'misfire_grace_time': 300  # 5 minutes grace time for missed jobs
        }
        
        # Create scheduler
        if self.scheduler_type == "blocking":
            self.scheduler = BlockingScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults
            )
        else:
            self.scheduler = BackgroundScheduler(
                jobstores=jobstores,
                executors=executors,
                job_defaults=job_defaults
            )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed, EVENT_JOB_MISSED)
        
        logger.info(f"Scheduler configured: type={self.scheduler_type}, executor={self.executor_type}")
    
    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down scheduler...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _job_executed(self, event):
        """Handle successful job execution."""
        self.job_stats["jobs_executed"] += 1
        self.job_stats["last_execution"] = datetime.now().isoformat()
        logger.info(f"Job {event.job_id} executed successfully")
    
    def _job_error(self, event):
        """Handle job execution errors."""
        self.job_stats["jobs_failed"] += 1
        self.job_stats["last_error"] = {
            "timestamp": datetime.now().isoformat(),
            "job_id": event.job_id,
            "exception": str(event.exception)
        }
        logger.error(f"Job {event.job_id} failed: {event.exception}")
    
    def _job_missed(self, event):
        """Handle missed job executions."""
        self.job_stats["jobs_missed"] += 1
        logger.warning(f"Job {event.job_id} missed execution at {event.scheduled_run_time}")
    
    def _pipeline_job_wrapper(self, job_config: Dict[str, Any]):
        """
        Wrapper function for pipeline jobs with error handling and logging.
        
        Args:
            job_config: Configuration for the pipeline job
        """
        job_id = job_config.get('job_id', 'unknown')
        logger.info(f"Starting pipeline job: {job_id}")
        
        try:
            # Import here to avoid circular imports and serialization issues
            from lets_talk.pipeline import create_vector_database
            from lets_talk.config import (
                DATA_DIR, VECTOR_STORAGE_PATH, FORCE_RECREATE, OUTPUT_DIR,
                USE_CHUNKING, SHOULD_SAVE_STATS, CHUNK_SIZE, CHUNK_OVERLAP,
                QDRANT_COLLECTION, EMBEDDING_MODEL, DEFAULT_METADATA_CSV_FILENAME
            )
            
            # Extract pipeline parameters
            data_dir = job_config.get('data_dir', DATA_DIR)
            storage_path = job_config.get('storage_path', VECTOR_STORAGE_PATH)
            force_recreate = job_config.get('force_recreate', FORCE_RECREATE)
            output_dir = job_config.get('output_dir', OUTPUT_DIR)
            ci_mode = job_config.get('ci_mode', True)  # Default to CI mode for scheduled jobs
            use_chunking = job_config.get('use_chunking', USE_CHUNKING)
            should_save_stats = job_config.get('should_save_stats', SHOULD_SAVE_STATS)
            chunk_size = job_config.get('chunk_size', CHUNK_SIZE)
            chunk_overlap = job_config.get('chunk_overlap', CHUNK_OVERLAP)
            collection_name = job_config.get('collection_name', QDRANT_COLLECTION)
            embedding_model = job_config.get('embedding_model', EMBEDDING_MODEL)
            data_dir_pattern = job_config.get('data_dir_pattern', "*.md")
            blog_base_url = job_config.get('blog_base_url')
            base_url = job_config.get('base_url')
            incremental_mode = job_config.get('incremental_mode', "auto")
            metadata_csv_path = job_config.get('metadata_csv_path')
            dry_run = job_config.get('dry_run', False)
            
            # Set default metadata CSV path if not provided
            if metadata_csv_path is None:
                metadata_csv_path = os.path.join(output_dir, DEFAULT_METADATA_CSV_FILENAME)
            
            # Execute the pipeline
            success, message, stats, stats_file, stats_content = create_vector_database(
                data_dir=data_dir,
                storage_path=storage_path,
                force_recreate=force_recreate,
                output_dir=output_dir,
                ci_mode=ci_mode,
                use_chunking=use_chunking,
                should_save_stats=should_save_stats,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                collection_name=collection_name,
                embedding_model=embedding_model,
                data_dir_pattern=data_dir_pattern,
                blog_base_url=blog_base_url,
                base_url=base_url,
                incremental_mode=incremental_mode,
                metadata_csv_path=metadata_csv_path,
                dry_run=dry_run
            )
            
            if success:
                logger.info(f"Pipeline job {job_id} completed successfully: {message}")
                if stats:
                    logger.info(f"Processed {stats['total_documents']} documents")
            else:
                logger.error(f"Pipeline job {job_id} failed: {message}")
                raise Exception(message)
                
            # Save job execution report
            self._save_job_report(job_id, success, message, stats, stats_file)
            
        except Exception as e:
            logger.error(f"Pipeline job {job_id} failed with exception: {str(e)}", exc_info=True)
            self._save_job_report(job_id, False, str(e), None, None)
            raise
    
    def _save_job_report(self, job_id: str, success: bool, message: str, 
                        stats: Optional[Dict], stats_file: Optional[str]):
        """Save a report of job execution."""
        report = {
            "job_id": job_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "message": message,
            "stats": stats,
            "stats_file": stats_file
        }
        
        report_file = Path(OUTPUT_DIR) / f"job_report_{job_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Job report saved: {report_file}")
    
    def add_cron_job(self, 
                     job_id: str,
                     cron_expression: Optional[str] = None,
                     hour: Optional[int] = None,
                     minute: int = 0,
                     day_of_week: Optional[str] = None,
                     pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a cron-based scheduled job.
        
        Args:
            job_id: Unique identifier for the job
            cron_expression: Full cron expression (if provided, overrides other params)
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
            day_of_week: Day of week (mon,tue,wed,thu,fri,sat,sun or 0-6)
            pipeline_config: Configuration dict for pipeline execution
            
        Returns:
            Job ID
        """
        if pipeline_config is None:
            pipeline_config = {}
        
        pipeline_config['job_id'] = job_id
        
        if cron_expression:
            # Parse full cron expression
            trigger = CronTrigger.from_crontab(cron_expression)
        else:
            # Build trigger from individual parameters
            trigger_kwargs: Dict[str, Any] = {'minute': minute}
            if hour is not None:
                trigger_kwargs['hour'] = hour
            if day_of_week is not None:
                # APScheduler accepts day_of_week as string
                trigger_kwargs['day_of_week'] = day_of_week
            
            trigger = CronTrigger(**trigger_kwargs)
        
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        
        # Use standalone job function to avoid serialization issues
        from lets_talk.pipeline_job import pipeline_job_function
        
        job = self.scheduler.add_job(
            func=pipeline_job_function,
            trigger=trigger,
            args=[pipeline_config],
            id=job_id,
            name=f"Pipeline Cron Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added cron job '{job_id}' with trigger: {trigger}")
        return job.id
    
    def add_interval_job(self,
                        job_id: str,
                        minutes: Optional[int] = None,
                        hours: Optional[int] = None,
                        days: Optional[int] = None,
                        pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Add an interval-based scheduled job.
        
        Args:
            job_id: Unique identifier for the job
            minutes: Interval in minutes
            hours: Interval in hours
            days: Interval in days
            pipeline_config: Configuration dict for pipeline execution
            
        Returns:
            Job ID
        """
        if pipeline_config is None:
            pipeline_config = {}
        
        pipeline_config['job_id'] = job_id
        
        # Build interval trigger
        trigger_kwargs = {}
        if minutes:
            trigger_kwargs['minutes'] = minutes
        if hours:
            trigger_kwargs['hours'] = hours
        if days:
            trigger_kwargs['days'] = days
        
        if not trigger_kwargs:
            raise ValueError("Must specify at least one interval (minutes, hours, or days)")
        
        trigger = IntervalTrigger(**trigger_kwargs)
        
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        
        # Use standalone job function to avoid serialization issues
        from lets_talk.pipeline_job import pipeline_job_function
        
        job = self.scheduler.add_job(
            func=pipeline_job_function,
            trigger=trigger,
            args=[pipeline_config],
            id=job_id,
            name=f"Pipeline Interval Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added interval job '{job_id}' with trigger: {trigger}")
        return job.id
    
    def add_one_time_job(self,
                        job_id: str,
                        run_date: datetime,
                        pipeline_config: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a one-time scheduled job.
        
        Args:
            job_id: Unique identifier for the job
            run_date: When to run the job
            pipeline_config: Configuration dict for pipeline execution
            
        Returns:
            Job ID
        """
        if pipeline_config is None:
            pipeline_config = {}
        
        pipeline_config['job_id'] = job_id
        
        trigger = DateTrigger(run_date=run_date)
        
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        
        # Use standalone job function to avoid serialization issues
        from lets_talk.pipeline_job import pipeline_job_function
        
        job = self.scheduler.add_job(
            func=pipeline_job_function,
            trigger=trigger,
            args=[pipeline_config],
            id=job_id,
            name=f"Pipeline One-time Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added one-time job '{job_id}' scheduled for: {run_date}")
        return job.id
    
    def remove_job(self, job_id: str):
        """Remove a scheduled job."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")
        except Exception as e:
            logger.error(f"Failed to remove job {job_id}: {e}")
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        jobs = []
        for job in self.scheduler.get_jobs():
            # next_run_time is only available after scheduler is started
            next_run_time = None
            if self.scheduler.running and hasattr(job, 'next_run_time') and job.next_run_time:
                next_run_time = job.next_run_time.isoformat()
            
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': next_run_time,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def get_job_stats(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        return self.job_stats.copy()
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.warning("Scheduler is already running")
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        if self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler shut down")
        else:
            logger.warning("Scheduler is not running")
    
    def run_job_now(self, job_id: str):
        """Run a specific job immediately."""
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                logger.info(f"Triggered immediate execution of job: {job_id}")
            else:
                logger.error(f"Job not found: {job_id}")
        except Exception as e:
            logger.error(f"Failed to run job {job_id}: {e}")
    
    def export_job_config(self) -> Dict[str, Any]:
        """
        Export current job configuration for backup/persistence.
        
        Returns:
            Dictionary containing job configurations that can be saved to file
        """
        if self.scheduler is None:
            return {"jobs": []}
        
        jobs_config = []
        jobs = self.scheduler.get_jobs()
        
        for job in jobs:
            job_data = {
                "job_id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            
            # Extract trigger information
            if hasattr(job.trigger, 'fields'):
                # For cron triggers
                if job.trigger.__class__.__name__ == 'CronTrigger':
                    job_data["type"] = "cron"
                    fields = job.trigger.fields
                    # Safely extract hour field
                    if len(fields) > 2 and hasattr(fields[2], 'expressions') and fields[2].expressions:
                        try:
                            hour_expr = list(fields[2].expressions)[0]
                            if hasattr(hour_expr, 'step') and hour_expr.step is None and hasattr(hour_expr, 'first'):
                                job_data["hour"] = hour_expr.first
                        except (IndexError, AttributeError):
                            pass
                    # Safely extract minute field
                    if len(fields) > 1 and hasattr(fields[1], 'expressions') and fields[1].expressions:
                        try:
                            minute_expr = list(fields[1].expressions)[0]
                            if hasattr(minute_expr, 'step') and minute_expr.step is None and hasattr(minute_expr, 'first'):
                                job_data["minute"] = minute_expr.first
                        except (IndexError, AttributeError):
                            pass
                    # Safely extract day_of_week field
                    if len(fields) > 4 and hasattr(fields[4], 'expressions') and fields[4].expressions:
                        try:
                            dow_expr = list(fields[4].expressions)[0]
                            if hasattr(dow_expr, 'step') and dow_expr.step is None and hasattr(dow_expr, 'first'):
                                job_data["day_of_week"] = dow_expr.first
                        except (IndexError, AttributeError):
                            pass
                        
            elif hasattr(job.trigger, 'interval'):
                # For interval triggers
                job_data["type"] = "interval"
                interval = job.trigger.interval
                if interval.days > 0:
                    job_data["days"] = interval.days
                if interval.seconds > 0:
                    hours = interval.seconds // 3600
                    minutes = (interval.seconds % 3600) // 60
                    seconds = interval.seconds % 60
                    if hours > 0:
                        job_data["hours"] = hours
                    if minutes > 0:
                        job_data["minutes"] = minutes
                    if seconds > 0:
                        job_data["seconds"] = seconds
                        
            elif hasattr(job.trigger, 'run_date'):
                # For date/one-time triggers
                job_data["type"] = "date"
                job_data["run_date"] = job.trigger.run_date.isoformat()
            
            # Extract pipeline config from job kwargs
            if hasattr(job, 'kwargs') and 'job_config' in job.kwargs:
                job_data["config"] = job.kwargs['job_config']
            
            jobs_config.append(job_data)
        
        return {
            "exported_at": datetime.now().isoformat(),
            "scheduler_stats": self.job_stats,
            "jobs": jobs_config
        }
    
    def import_job_config(self, config: Dict[str, Any]):
        """
        Import job configuration from exported config.
        
        Args:
            config: Configuration dictionary from export_job_config()
        """
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        
        jobs_data = config.get("jobs", [])
        imported_count = 0
        
        for job_data in jobs_data:
            try:
                job_id = job_data["job_id"]
                job_type = job_data.get("type", "interval")
                pipeline_config = job_data.get("config", {})
                
                # Skip if job already exists
                if self.scheduler.get_job(job_id):
                    logger.warning(f"Job {job_id} already exists, skipping import")
                    continue
                
                # Add job based on type
                if job_type == "cron":
                    self.add_cron_job(
                        job_id=job_id,
                        hour=job_data.get("hour"),
                        minute=job_data.get("minute", 0),
                        day_of_week=job_data.get("day_of_week"),
                        pipeline_config=pipeline_config
                    )
                elif job_type == "interval":
                    kwargs = {}
                    if "days" in job_data:
                        kwargs["days"] = job_data["days"]
                    if "hours" in job_data:
                        kwargs["hours"] = job_data["hours"]
                    if "minutes" in job_data:
                        kwargs["minutes"] = job_data["minutes"]
                    if "seconds" in job_data:
                        kwargs["seconds"] = job_data["seconds"]
                    
                    if not kwargs:  # Default to 1 hour if no interval specified
                        kwargs["hours"] = 1
                    
                    self.add_interval_job(
                        job_id=job_id,
                        pipeline_config=pipeline_config,
                        **kwargs
                    )
                elif job_type == "date" and "run_date" in job_data:
                    run_date = datetime.fromisoformat(job_data["run_date"])
                    if run_date > datetime.now():  # Only import future one-time jobs
                        self.add_one_time_job(
                            job_id=job_id,
                            run_date=run_date,
                            pipeline_config=pipeline_config
                        )
                
                imported_count += 1
                logger.info(f"Imported job: {job_id}")
                
            except Exception as e:
                logger.error(f"Failed to import job {job_data.get('job_id', 'unknown')}: {e}")
        
        logger.info(f"Imported {imported_count} jobs from configuration")
        return imported_count
    
    def add_simple_pipeline_job(self,
                               job_id: str,
                               schedule_type: str = "interval",
                               pipeline_config: Optional[Dict[str, Any]] = None,
                               **schedule_kwargs) -> str:
        """
        Add a pipeline job using the simplified job function that avoids import issues.
        
        Args:
            job_id: Unique identifier for the job
            schedule_type: "interval", "cron", or "date"
            pipeline_config: Configuration dict for pipeline execution
            **schedule_kwargs: Schedule-specific parameters (minutes, hours, day_of_week, etc.)
            
        Returns:
            Job ID
        """
        if pipeline_config is None:
            pipeline_config = {}
        
        pipeline_config['job_id'] = job_id
        
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
        
        # Import the simple job function that can be safely serialized
        from lets_talk.simple_pipeline_job import simple_pipeline_job
        
        # Build trigger based on schedule type
        if schedule_type == "interval":
            trigger = IntervalTrigger(**{k: v for k, v in schedule_kwargs.items() 
                                       if k in ['weeks', 'days', 'hours', 'minutes', 'seconds']})
        elif schedule_type == "cron":
            trigger = CronTrigger(**{k: v for k, v in schedule_kwargs.items() 
                                   if k in ['year', 'month', 'day', 'week', 'day_of_week', 'hour', 'minute', 'second']})
        elif schedule_type == "date":
            if 'run_date' not in schedule_kwargs:
                raise ValueError("run_date required for date trigger")
            trigger = DateTrigger(run_date=schedule_kwargs['run_date'])
        else:
            raise ValueError(f"Unsupported schedule type: {schedule_type}")
        
        job = self.scheduler.add_job(
            func=simple_pipeline_job,
            trigger=trigger,
            args=[pipeline_config],
            id=job_id,
            name=f"Simple Pipeline Job: {job_id}",
            replace_existing=True
        )
        
        logger.info(f"Added simple pipeline job '{job_id}' with {schedule_type} trigger: {trigger}")
        return job.id
    


def create_default_scheduler_config() -> Dict[str, Any]:
    """Create a default configuration for common scheduling scenarios."""
    return {
        "jobs": [
            {
                "job_id": "daily_incremental_update",
                "type": "cron",
                "hour": 2,  # 2 AM daily
                "minute": 0,
                "config": {
                    "incremental_mode": "auto",
                    "force_recreate": False,
                    "ci_mode": True
                }
            },
            {
                "job_id": "weekly_full_rebuild",
                "type": "cron",
                "day_of_week": "sun",  # Sunday
                "hour": 1,  # 1 AM
                "minute": 0,
                "config": {
                    "incremental_mode": "full",
                    "force_recreate": True,
                    "ci_mode": True
                }
            },
            {
                "job_id": "hourly_check",
                "type": "interval",
                "hours": 1,
                "config": {
                    "incremental_mode": "auto",
                    "dry_run": True,  # Just check for changes
                    "ci_mode": True
                }
            }
        ]
    }


def load_scheduler_config_from_file(config_file: str) -> Dict[str, Any]:
    """Load scheduler configuration from a JSON file."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load scheduler config from {config_file}: {e}")
        return create_default_scheduler_config()


def save_scheduler_config_to_file(config: Dict[str, Any], config_file: str):
    """Save scheduler configuration to a JSON file."""
    try:
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Scheduler config saved to: {config_file}")
    except Exception as e:
        logger.error(f"Failed to save scheduler config to {config_file}: {e}")
