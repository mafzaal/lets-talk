# Default Pipeline Job Configuration

## Overview

The application now supports automatic creation of a default pipeline job when the application starts. This ensures that there's always at least one scheduled pipeline job running without manual configuration.

## Configuration

The default job behavior is controlled by environment variables:

### Environment Variables

| Variable | Description | Default Value | Type |
|----------|-------------|---------------|------|
| `DEFAULT_JOB_ENABLED` | Enable/disable default job creation | `True` | boolean |
| `DEFAULT_JOB_ID` | Unique identifier for the default job | `default_pipeline_job` | string |
| `DEFAULT_JOB_CRON_HOUR` | Hour for cron schedule (0-23) | `2` | integer |
| `DEFAULT_JOB_CRON_MINUTE` | Minute for cron schedule (0-59) | `0` | integer |
| `DEFAULT_JOB_INCREMENTAL_MODE` | Pipeline incremental mode | `auto` | string |
| `DEFAULT_JOB_CI_MODE` | Enable CI mode for the default job | `False` | boolean |
| `DEFAULT_JOB_DRY_RUN` | Enable dry run mode | `False` | boolean |

### Example Configuration

```bash
# Enable default job scheduling
DEFAULT_JOB_ENABLED=True

# Schedule for 3:30 AM daily
DEFAULT_JOB_CRON_HOUR=3
DEFAULT_JOB_CRON_MINUTE=30

# Use full rebuild mode
DEFAULT_JOB_INCREMENTAL_MODE=full

# Disable CI mode for production
DEFAULT_JOB_CI_MODE=False
```

## How It Works

### Startup Process

1. **Application Start**: When the FastAPI application starts, it initializes the scheduler
2. **Check Configuration**: If `DEFAULT_JOB_ENABLED=True`, proceed with default job setup
3. **Job Existence Check**: Check if a job with `DEFAULT_JOB_ID` already exists
4. **Job Creation**: If no default job exists, create one with:
   - Cron schedule based on `DEFAULT_JOB_CRON_HOUR` and `DEFAULT_JOB_CRON_MINUTE`
   - Default pipeline configuration from `JobConfig.with_defaults()`
   - Override settings from default job environment variables
5. **Skip Creation**: If default job already exists, skip creation and log info

### Default Job Configuration

The default job uses:
- **Schedule**: Daily cron job at the configured time (default: 2:00 AM)
- **Pipeline Config**: All default values from `JobConfig.with_defaults()`
- **Incremental Mode**: Configurable via `DEFAULT_JOB_INCREMENTAL_MODE` (default: "auto")
- **CI Mode**: Configurable via `DEFAULT_JOB_CI_MODE` (default: True)
- **Stats Saving**: Always enabled (`should_save_stats: True`)
- **Force Recreate**: Always disabled (`force_recreate: False`)

## Management

### Viewing the Default Job

The default job appears in the scheduler interface with:
- **Job ID**: `default_pipeline_job` (or configured value)
- **Name**: `Cron Job: default_pipeline_job`
- **Schedule**: Daily at configured time

### API Access

You can manage the default job through the scheduler API like any other job:

```bash
# View all jobs (including default)
curl "http://localhost:2024/scheduler/jobs"

# Run default job immediately
curl -X POST "http://localhost:2024/scheduler/jobs/default_pipeline_job/run"

# Remove default job (will be recreated on next restart if enabled)
curl -X DELETE "http://localhost:2024/scheduler/jobs/default_pipeline_job"
```

### Frontend Interface

The default job appears in the frontend scheduler interface and can be:
- Viewed in the jobs list
- Edited like any other job
- Triggered manually
- Removed (though it will be recreated on restart if enabled)

## Disabling Default Job

To disable automatic default job creation:

```bash
# Disable default job creation
DEFAULT_JOB_ENABLED=False
```

Or remove/comment out the variable entirely to use the default (`True`).

## Troubleshooting

### Common Issues

1. **Default job not created**
   - Check that `DEFAULT_JOB_ENABLED=True`
   - Check application logs for errors during startup
   - Verify database connectivity if using persistent storage

2. **Multiple default jobs**
   - Ensure `DEFAULT_JOB_ID` is unique
   - Check for manual job creation with the same ID

3. **Wrong schedule time**
   - Verify `DEFAULT_JOB_CRON_HOUR` and `DEFAULT_JOB_CRON_MINUTE` values
   - Remember that hours are in 24-hour format (0-23)

### Logs

The application logs default job activity:

```
INFO:lets_talk.scheduler:Creating default pipeline job...
INFO:lets_talk.scheduler:Created default pipeline job 'default_pipeline_job' scheduled for 02:00
INFO:lets_talk.scheduler:Default pipeline job created successfully
```

Or if the job already exists:
```
INFO:lets_talk.scheduler:Default job 'default_pipeline_job' already exists
```

## Implementation Details

### Code Structure

- **Configuration**: `/backend/lets_talk/shared/config.py`
- **Scheduler Manager**: `/backend/lets_talk/core/scheduler/manager.py`
- **App Startup**: `/backend/lets_talk/api/main.py`

### Key Methods

- `PipelineScheduler.has_default_job()`: Check if default job exists
- `PipelineScheduler.create_default_job()`: Create the default job
- `PipelineScheduler.initialize_default_job_if_needed()`: Main initialization method

### Safety Features

- **Non-blocking**: Default job creation failure doesn't prevent app startup
- **Idempotent**: Multiple calls to initialize don't create duplicate jobs
- **Configurable**: All aspects controlled by environment variables
- **Logging**: Comprehensive logging for debugging and monitoring
