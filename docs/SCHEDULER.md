# Pipeline Scheduler Documentation

## Overview

The Pipeline Scheduler provides automated, scheduled execution of the blog data pipeline using APScheduler with executor pools. It supports various scheduling patterns, persistent job storage, error handling, and monitoring.

## Features

- **Multiple Scheduling Types**: Cron-style, interval-based, and one-time scheduling
- **Executor Pools**: Thread and process pool executors for concurrent job execution
- **Persistent Storage**: SQLite-based job storage that survives application restarts
- **Error Handling**: Comprehensive error handling with retries and logging
- **Monitoring**: Job execution statistics and health reporting
- **CLI Management**: Full command-line interface for managing scheduled jobs
- **Configuration**: JSON-based configuration for easy job management

## Installation

The scheduler is automatically available when APScheduler is installed:

```bash
uv add apscheduler
```

## Usage

### 1. CLI Interface

The scheduler can be managed via the command-line interface:

```bash
# Start scheduler with default configuration
cd py-src && uv run python -m lets_talk.core.scheduler.cli start

# Start scheduler in daemon mode
cd py-src && uv run python -m lets_talk.core.scheduler.cli start --daemon

# Show scheduler status and jobs
cd py-src && uv run python -m lets_talk.core.scheduler.cli status

# Add a daily job at 2 AM
cd py-src && uv run python -m lets_talk.core.scheduler.cli add-job --type cron --id daily_update --hour 2 --minute 0

# Add an hourly interval job
cd py-src && uv run python -m lets_talk.core.scheduler.cli add-job --type interval --id hourly_check --hours 1

# Remove a job
cd py-src && uv run python -m lets_talk.core.scheduler.cli remove-job --id daily_update

# Run a job immediately
python -m lets_talk.scheduler_cli run-now --id daily_update

# Stop the scheduler
python -m lets_talk.scheduler_cli stop
```

### 2. Integrated Pipeline Execution

Run the pipeline with built-in scheduling:

```bash
# Start pipeline in scheduled mode with default config
python pipeline.py --schedule

# Start pipeline in scheduled daemon mode
python pipeline.py --schedule --schedule-daemon

# Use custom scheduler configuration
python pipeline.py --schedule --schedule-config /path/to/config.json
```

### 3. Programmatic Usage

```python
from lets_talk.core.scheduler.manager import PipelineScheduler
from datetime import datetime

# Create scheduler
scheduler = PipelineScheduler(
    scheduler_type="background",
    max_workers=4,
    executor_type="thread",
    enable_persistence=True
)

# Add a daily job
scheduler.add_cron_job(
    job_id="daily_update",
    hour=2,
    minute=0,
    pipeline_config={
        "incremental_mode": "auto",
        "ci_mode": True
    }
)

# Add an interval job (every 6 hours)
scheduler.add_interval_job(
    job_id="interval_check",
    hours=6,
    pipeline_config={
        "dry_run": True
    }
)

# Start scheduler
scheduler.start()

# Keep running (for background scheduler)
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    scheduler.shutdown()
```

## Configuration

### Configuration File Format

The scheduler uses JSON configuration files to define jobs:

```json
{
  "jobs": [
    {
      "job_id": "daily_incremental_update",
      "type": "cron",
      "hour": 2,
      "minute": 0,
      "config": {
        "incremental_mode": "auto",
        "force_recreate": false,
        "ci_mode": true
      }
    },
    {
      "job_id": "weekly_full_rebuild", 
      "type": "cron",
      "day_of_week": "sun",
      "hour": 1,
      "minute": 0,
      "config": {
        "incremental_mode": "full",
        "force_recreate": true,
        "ci_mode": true
      }
    },
    {
      "job_id": "hourly_health_check",
      "type": "interval", 
      "hours": 1,
      "config": {
        "dry_run": true,
        "ci_mode": true
      }
    }
  ]
}
```

### Job Types

#### 1. Cron Jobs

Schedule jobs using cron-style expressions:

```json
{
  "job_id": "daily_job",
  "type": "cron",
  "hour": 2,        // 0-23
  "minute": 30,     // 0-59 
  "day_of_week": "mon,wed,fri",  // Optional
  "config": { ... }
}
```

Or use full cron expressions:

```json
{
  "job_id": "complex_schedule",
  "type": "cron",
  "cron_expression": "0 2 * * 1-5",  // 2 AM, Monday-Friday
  "config": { ... }
}
```

#### 2. Interval Jobs

Schedule jobs to run at regular intervals:

```json
{
  "job_id": "interval_job",
  "type": "interval",
  "minutes": 30,    // Every 30 minutes
  "hours": 2,       // Every 2 hours  
  "days": 1,        // Every day
  "config": { ... }
}
```

#### 3. One-time Jobs

Schedule jobs to run once at a specific time:

```json
{
  "job_id": "one_time_job",
  "type": "date",
  "run_date": "2025-06-20T15:30:00",
  "config": { ... }
}
```

### Pipeline Configuration

Each job can specify pipeline-specific configuration:

```json
{
  "config": {
    "data_dir": "/path/to/data",
    "storage_path": "/path/to/vector/store", 
    "force_recreate": false,
    "incremental_mode": "auto",
    "ci_mode": true,
    "dry_run": false,
    "use_chunking": true,
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "collection_name": "blog_posts",
    "embedding_model": "text-embedding-3-small"
  }
}
```

## Scheduler Components

### 1. PipelineScheduler Class

Main scheduler class with the following components:

- **Job Stores**: SQLite (persistent) or Memory (temporary)
- **Executors**: ThreadPoolExecutor or ProcessPoolExecutor  
- **Triggers**: Cron, Interval, or Date triggers
- **Event Listeners**: Job execution monitoring and logging

### 2. Executor Pools

Choose between thread or process pool executors:

```python
# Thread pool (default) - good for I/O bound tasks
scheduler = PipelineScheduler(executor_type="thread", max_workers=4)

# Process pool - good for CPU bound tasks  
scheduler = PipelineScheduler(executor_type="process", max_workers=2)
```

### 3. Persistent Storage

Jobs are persisted to SQLite database by default:

```python
# Enable persistence (default)
scheduler = PipelineScheduler(enable_persistence=True)

# Custom database location
scheduler = PipelineScheduler(
    enable_persistence=True,
    job_store_url="sqlite:///path/to/scheduler.db"
)

# Memory only (jobs lost on restart)
scheduler = PipelineScheduler(enable_persistence=False)
```

## Monitoring and Logging

### Job Statistics

Get execution statistics:

```python
stats = scheduler.get_job_stats()
print(f"Jobs executed: {stats['jobs_executed']}")
print(f"Jobs failed: {stats['jobs_failed']}")
print(f"Jobs missed: {stats['jobs_missed']}")
```

### Job Reports

Each job execution generates a detailed report saved to the output directory:

```
{output_dir}/job_report_{job_id}_{timestamp}.json
```

### Logging

All scheduler activities are logged with appropriate levels:

- INFO: Job scheduling, execution, and status changes
- WARNING: Missed jobs and non-critical issues  
- ERROR: Job failures and critical errors

## Error Handling

### Automatic Retry

Jobs have built-in retry mechanisms:

- **Coalesce**: Multiple pending executions are combined into one
- **Max Instances**: Limit concurrent job instances  
- **Misfire Grace Time**: 5-minute grace period for missed jobs

### Exception Handling

All job exceptions are caught and logged:

```python
def _job_error(self, event):
    """Handle job execution errors."""
    self.job_stats["jobs_failed"] += 1
    self.job_stats["last_error"] = {
        "timestamp": datetime.now().isoformat(),
        "job_id": event.job_id,
        "exception": str(event.exception)
    }
    logger.error(f"Job {event.job_id} failed: {event.exception}")
```

## Best Practices

### 1. Job Naming

Use descriptive, hierarchical job IDs:

```
daily_incremental_update
weekly_full_rebuild  
hourly_health_check
monthly_cleanup
```

### 2. Resource Management

- Use thread pools for I/O-bound pipeline operations
- Limit concurrent workers to avoid resource contention
- Monitor memory usage with large document sets

### 3. Configuration Management

- Store configurations in version control
- Use environment-specific configs for dev/staging/prod
- Validate configurations before deployment

### 4. Monitoring

- Set up log aggregation for production deployments
- Monitor job execution statistics
- Set up alerts for failed jobs

### 5. Backup and Recovery

- Backup job store database regularly
- Keep configuration files in version control
- Document recovery procedures

## Examples

### Basic Daily Pipeline

```bash
# Create configuration
python -m lets_talk.scheduler_cli config --action create

# Start scheduler  
python -m lets_talk.scheduler_cli start --daemon

# Check status
python -m lets_talk.scheduler_cli status
```

### Custom Scheduling

```python
from lets_talk.scheduler import PipelineScheduler

scheduler = PipelineScheduler()

# Business hours incremental updates (9 AM - 5 PM, weekdays)
scheduler.add_cron_job(
    job_id="business_hours_update",
    hour="9-17",
    day_of_week="mon-fri",
    pipeline_config={"incremental_mode": "auto"}
)

# Weekend full rebuild
scheduler.add_cron_job(
    job_id="weekend_rebuild",
    day_of_week="sat",
    hour=2,
    pipeline_config={"force_recreate": True}
)

scheduler.start()
```

### Development and Testing

```python
# Development mode - frequent dry runs
scheduler.add_interval_job(
    job_id="dev_check",
    minutes=15,
    pipeline_config={"dry_run": True}
)

# Test specific pipeline configuration
test_config = {
    "data_dir": "test_data/",
    "storage_path": "test_vector_store/",
    "ci_mode": True
}

scheduler.add_one_time_job(
    job_id="test_run",
    run_date=datetime.now() + timedelta(minutes=1),
    pipeline_config=test_config
)
```

## Troubleshooting

### Common Issues

1. **Jobs not executing**: Check scheduler is running and job triggers are correct
2. **High memory usage**: Reduce max_workers or use process executor
3. **Database locks**: Ensure only one scheduler instance per database
4. **Missing dependencies**: Verify APScheduler is installed

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('apscheduler').setLevel(logging.DEBUG)
```

### Health Checks

Use the built-in health check:

```bash
python pipeline.py --health-check-only
```

## Production Deployment

### Systemd Service

Create a systemd service for production:

```ini
[Unit]
Description=Blog Pipeline Scheduler
After=network.target

[Service]
Type=simple
User=pipeline
WorkingDirectory=/opt/lets-talk
ExecStart=/opt/lets-talk/venv/bin/python -m lets_talk.scheduler_cli start --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker Container

```dockerfile
FROM python:3.13
COPY . /app
WORKDIR /app
RUN uv install
CMD ["python", "-m", "lets_talk.scheduler_cli", "start", "--daemon"]
```

### Monitoring Integration

Integrate with monitoring systems:

```python
# Custom metrics export
stats = scheduler.get_job_stats()
# Send to Prometheus, DataDog, etc.
```

This scheduler implementation provides a robust, production-ready solution for automating your blog data pipeline with comprehensive monitoring, error handling, and management capabilities.
