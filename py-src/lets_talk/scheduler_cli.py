#!/usr/bin/env python3
"""
Pipeline Scheduler CLI

Command-line interface for managing scheduled pipeline execution.

Usage:
    python scheduler_cli.py [command] [options]

Commands:
    start       Start the scheduler daemon
    stop        Stop the scheduler daemon
    status      Show scheduler status and jobs
    add-job     Add a new scheduled job
    remove-job  Remove a scheduled job
    run-now     Run a job immediately
    config      Manage scheduler configuration

Examples:
    # Start scheduler with default configuration
    python scheduler_cli.py start

    # Add a daily job at 2 AM
    python scheduler_cli.py add-job --type cron --id daily_update --hour 2 --minute 0

    # Add an hourly interval job
    python scheduler_cli.py add-job --type interval --id hourly_check --hours 1

    # Show all jobs and status
    python scheduler_cli.py status

    # Run a job immediately
    python scheduler_cli.py run-now --id daily_update
"""

import argparse
import json
import sys
import time
import signal
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import our scheduler module
from lets_talk.scheduler import (
    PipelineScheduler, 
    create_default_scheduler_config,
    load_scheduler_config_from_file,
    save_scheduler_config_to_file
)
from lets_talk.config import OUTPUT_DIR, LOGGER_NAME
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(f"{LOGGER_NAME}.scheduler_cli")

class SchedulerCLI:
    """Command-line interface for the pipeline scheduler."""
    
    def __init__(self):
        self.scheduler = None
        self.config_file = os.path.join(OUTPUT_DIR, "scheduler_config.json")
        self.pid_file = os.path.join(OUTPUT_DIR, "scheduler.pid")
        
    def start_scheduler(self, args):
        """Start the scheduler daemon."""
        
        # Check if scheduler is already running
        if self._is_scheduler_running():
            print("Scheduler is already running")
            return 1
        
        # Load configuration
        config = self._load_config(args.config_file)
        
        # Create scheduler
        self.scheduler = PipelineScheduler(
            scheduler_type="background" if args.daemon else "blocking",
            max_workers=args.max_workers,
            executor_type=args.executor_type,
            enable_persistence=args.enable_persistence
        )
        
        # Add jobs from configuration
        self._setup_jobs_from_config(config)
        
        # Start scheduler
        self.scheduler.start()
        
        if args.daemon:
            # Write PID file
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            
            print(f"Scheduler started in daemon mode (PID: {os.getpid()})")
            print(f"Jobs configured: {len(self.scheduler.list_jobs())}")
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
        else:
            print("Starting scheduler in blocking mode...")
            print(f"Jobs configured: {len(self.scheduler.list_jobs())}")
            try:
                # Blocking mode - scheduler.start() will block here
                pass
            except KeyboardInterrupt:
                print("\nShutting down scheduler...")
        
        # Cleanup
        if self.scheduler:
            self.scheduler.shutdown()
        self._cleanup_pid_file()
        return 0
    
    def stop_scheduler(self, args):
        """Stop the scheduler daemon."""
        if not self._is_scheduler_running():
            print("Scheduler is not running")
            return 1
        
        # Read PID and send termination signal
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            os.kill(pid, signal.SIGTERM)
            print(f"Sent termination signal to scheduler (PID: {pid})")
            
            # Wait for process to stop
            for _ in range(10):
                if not self._is_scheduler_running():
                    print("Scheduler stopped successfully")
                    return 0
                time.sleep(0.5)
            
            # Force kill if still running
            os.kill(pid, signal.SIGKILL)
            print("Force killed scheduler")
            
        except (FileNotFoundError, ProcessLookupError):
            print("Scheduler process not found")
        except Exception as e:
            print(f"Error stopping scheduler: {e}")
            return 1
        
        self._cleanup_pid_file()
        return 0
    
    def show_status(self, args):
        """Show scheduler status and jobs."""
        is_running = self._is_scheduler_running()
        
        print(f"Scheduler Status: {'RUNNING' if is_running else 'STOPPED'}")
        
        if is_running:
            try:
                with open(self.pid_file, 'r') as f:
                    pid = f.read().strip()
                print(f"PID: {pid}")
            except FileNotFoundError:
                pass
        
        # Try to connect to scheduler to get job info
        try:
            temp_scheduler = PipelineScheduler(scheduler_type="background", enable_persistence=True)
            jobs = temp_scheduler.list_jobs()
            stats = temp_scheduler.get_job_stats()
            
            print(f"\nJobs: {len(jobs)}")
            for job in jobs:
                print(f"  - {job['id']}: {job['name']}")
                print(f"    Next run: {job['next_run_time'] or 'Not scheduled'}")
                print(f"    Trigger: {job['trigger']}")
            
            print(f"\nJob Statistics:")
            print(f"  Executed: {stats['jobs_executed']}")
            print(f"  Failed: {stats['jobs_failed']}")
            print(f"  Missed: {stats['jobs_missed']}")
            print(f"  Last execution: {stats['last_execution'] or 'None'}")
            
            temp_scheduler.shutdown()
            
        except Exception as e:
            print(f"Could not retrieve job information: {e}")
        
        return 0
    
    def add_job(self, args):
        """Add a new scheduled job."""
        try:
            scheduler = PipelineScheduler(scheduler_type="background", enable_persistence=True)
            
            # Build pipeline configuration
            pipeline_config = {}
            if args.data_dir:
                pipeline_config['data_dir'] = args.data_dir
            if args.storage_path:
                pipeline_config['storage_path'] = args.storage_path
            if args.force_recreate:
                pipeline_config['force_recreate'] = True
            if args.incremental_mode:
                pipeline_config['incremental_mode'] = args.incremental_mode
            if args.dry_run:
                pipeline_config['dry_run'] = True
            
            # Add job based on type
            if args.type == "cron":
                if args.cron_expression:
                    job_id = scheduler.add_cron_job(
                        job_id=args.id,
                        cron_expression=args.cron_expression,
                        pipeline_config=pipeline_config
                    )
                else:
                    job_id = scheduler.add_cron_job(
                        job_id=args.id,
                        hour=args.hour,
                        minute=args.minute,
                        day_of_week=args.day_of_week,
                        pipeline_config=pipeline_config
                    )
            elif args.type == "interval":
                job_id = scheduler.add_interval_job(
                    job_id=args.id,
                    minutes=args.minutes,
                    hours=args.hours,
                    days=args.days,
                    pipeline_config=pipeline_config
                )
            elif args.type == "date":
                if not args.run_date:
                    print("--run-date is required for date jobs")
                    return 1
                
                run_date = datetime.fromisoformat(args.run_date)
                job_id = scheduler.add_one_time_job(
                    job_id=args.id,
                    run_date=run_date,
                    pipeline_config=pipeline_config
                )
            else:
                print(f"Unknown job type: {args.type}")
                return 1
            
            print(f"Job '{job_id}' added successfully")
            scheduler.shutdown()
            return 0
            
        except Exception as e:
            print(f"Error adding job: {e}")
            return 1
    
    def remove_job(self, args):
        """Remove a scheduled job."""
        try:
            scheduler = PipelineScheduler(scheduler_type="background", enable_persistence=True)
            scheduler.remove_job(args.id)
            print(f"Job '{args.id}' removed successfully")
            scheduler.shutdown()
            return 0
        except Exception as e:
            print(f"Error removing job: {e}")
            return 1
    
    def run_job_now(self, args):
        """Run a job immediately."""
        try:
            scheduler = PipelineScheduler(scheduler_type="background", enable_persistence=True)
            scheduler.run_job_now(args.id)
            print(f"Job '{args.id}' triggered for immediate execution")
            scheduler.shutdown()
            return 0
        except Exception as e:
            print(f"Error running job: {e}")
            return 1
    
    def manage_config(self, args):
        """Manage scheduler configuration."""
        if args.config_action == "create":
            config = create_default_scheduler_config()
            save_scheduler_config_to_file(config, self.config_file)
            print(f"Default configuration created: {self.config_file}")
            
        elif args.config_action == "show":
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                print(json.dumps(config, indent=2))
            else:
                print("No configuration file found")
                
        elif args.config_action == "validate":
            try:
                config = load_scheduler_config_from_file(self.config_file)
                print("Configuration is valid")
                print(f"Jobs defined: {len(config.get('jobs', []))}")
            except Exception as e:
                print(f"Configuration validation failed: {e}")
                return 1
        
        return 0
    
    def _is_scheduler_running(self):
        """Check if scheduler is currently running."""
        if not os.path.exists(self.pid_file):
            return False
        
        try:
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
            
            # Check if process exists
            os.kill(pid, 0)
            return True
            
        except (FileNotFoundError, ProcessLookupError, ValueError):
            self._cleanup_pid_file()
            return False
    
    def _cleanup_pid_file(self):
        """Remove the PID file."""
        try:
            os.remove(self.pid_file)
        except FileNotFoundError:
            pass
    
    def _load_config(self, config_file):
        """Load scheduler configuration."""
        if config_file and os.path.exists(config_file):
            return load_scheduler_config_from_file(config_file)
        elif os.path.exists(self.config_file):
            return load_scheduler_config_from_file(self.config_file)
        else:
            print("No configuration file found, using default configuration")
            return create_default_scheduler_config()
    
    def _setup_jobs_from_config(self, config):
        """Set up jobs from configuration."""
        if self.scheduler is None:
            logger.error("Scheduler not initialized")
            return
            
        jobs = config.get('jobs', [])
        for job_config in jobs:
            try:
                job_type = job_config.get('type')
                job_id = job_config.get('job_id')
                pipeline_config = job_config.get('config', {})
                
                if job_type == "cron":
                    self.scheduler.add_cron_job(
                        job_id=job_id,
                        hour=job_config.get('hour'),
                        minute=job_config.get('minute', 0),
                        day_of_week=job_config.get('day_of_week'),
                        pipeline_config=pipeline_config
                    )
                elif job_type == "interval":
                    self.scheduler.add_interval_job(
                        job_id=job_id,
                        minutes=job_config.get('minutes'),
                        hours=job_config.get('hours'),
                        days=job_config.get('days'),
                        pipeline_config=pipeline_config
                    )
                
                logger.info(f"Added job from config: {job_id}")
                
            except Exception as e:
                logger.error(f"Failed to add job from config: {e}")


def create_parser():
    """Create the argument parser."""
    parser = argparse.ArgumentParser(description="Pipeline Scheduler CLI")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the scheduler')
    start_parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    start_parser.add_argument('--config-file', help='Configuration file path')
    start_parser.add_argument('--max-workers', type=int, default=4, help='Maximum worker threads')
    start_parser.add_argument('--executor-type', choices=['thread', 'process'], default='thread')
    start_parser.add_argument('--enable-persistence', action='store_true', default=True)
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the scheduler')
    
    # Status command
    subparsers.add_parser('status', help='Show scheduler status')
    
    # Add job command
    add_parser = subparsers.add_parser('add-job', help='Add a scheduled job')
    add_parser.add_argument('--id', required=True, help='Job ID')
    add_parser.add_argument('--type', choices=['cron', 'interval', 'date'], required=True)
    
    # Cron options
    add_parser.add_argument('--cron-expression', help='Full cron expression')
    add_parser.add_argument('--hour', type=int, help='Hour (0-23)')
    add_parser.add_argument('--minute', type=int, default=0, help='Minute (0-59)')
    add_parser.add_argument('--day-of-week', help='Day of week')
    
    # Interval options
    add_parser.add_argument('--minutes', type=int, help='Interval in minutes')
    add_parser.add_argument('--hours', type=int, help='Interval in hours')
    add_parser.add_argument('--days', type=int, help='Interval in days')
    
    # Date options
    add_parser.add_argument('--run-date', help='Run date (ISO format)')
    
    # Pipeline options
    add_parser.add_argument('--data-dir', help='Data directory')
    add_parser.add_argument('--storage-path', help='Vector storage path')
    add_parser.add_argument('--force-recreate', action='store_true')
    add_parser.add_argument('--incremental-mode', help='Incremental mode')
    add_parser.add_argument('--dry-run', action='store_true')
    
    # Remove job command
    remove_parser = subparsers.add_parser('remove-job', help='Remove a job')
    remove_parser.add_argument('--id', required=True, help='Job ID')
    
    # Run now command
    run_parser = subparsers.add_parser('run-now', help='Run a job immediately')
    run_parser.add_argument('--id', required=True, help='Job ID')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--action', dest='config_action', 
                              choices=['create', 'show', 'validate'], 
                              required=True)
    
    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    cli = SchedulerCLI()
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        if args.command == 'start':
            return cli.start_scheduler(args)
        elif args.command == 'stop':
            return cli.stop_scheduler(args)
        elif args.command == 'status':
            return cli.show_status(args)
        elif args.command == 'add-job':
            return cli.add_job(args)
        elif args.command == 'remove-job':
            return cli.remove_job(args)
        elif args.command == 'run-now':
            return cli.run_job_now(args)
        elif args.command == 'config':
            return cli.manage_config(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
            
    except KeyboardInterrupt:
        print("\nOperation cancelled")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
